from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import hashlib
import secrets
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.core.token_cipher import FernetTokenCipher, TokenCipherError
from app.integrations.google_oauth import GoogleOAuthError, GoogleOAuthTokenResponse, GoogleOAuthWebClient
from app.models.provider_connection import ProviderConnection
from app.models.provider_oauth_state import ProviderOAuthState
from app.repositories.business_repository import BusinessRepository
from app.repositories.principal_repository import PrincipalRepository
from app.repositories.provider_connection_repository import ProviderConnectionRepository
from app.repositories.provider_oauth_state_repository import ProviderOAuthStateRepository
from app.services.auth_audit import AuthAuditService


class GoogleBusinessProfileConnectionNotFoundError(ValueError):
    pass


class GoogleBusinessProfileConnectionConfigurationError(ValueError):
    pass


class GoogleBusinessProfileConnectionValidationError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class GoogleBusinessProfileConnectStartResult:
    authorization_url: str
    state_expires_at: str
    provider: str
    required_scope: str


@dataclass(frozen=True)
class GoogleBusinessProfileConnectionStatusResult:
    connected: bool
    provider: str
    business_id: str
    principal_id: str | None
    scopes: tuple[str, ...]
    access_token_expires_at: str | None
    connected_at: str | None
    updated_at: str | None
    last_error: str | None


class GoogleBusinessProfileConnectionService:
    PROVIDER = "google_business_profile"
    BUSINESS_PROFILE_SCOPE = "https://www.googleapis.com/auth/business.manage"

    TARGET_TYPE = "integration_connection"
    EVENT_CONNECT_STARTED = "integration_google_business_profile_connect_started"
    EVENT_CONNECT_SUCCEEDED = "integration_google_business_profile_connected"
    EVENT_CONNECT_DENIED = "integration_google_business_profile_connect_denied"
    EVENT_CONNECT_FAILED = "integration_google_business_profile_connect_failed"
    EVENT_DISCONNECTED = "integration_google_business_profile_disconnected"
    EVENT_CALLBACK_REPLAYED = "integration_google_business_profile_callback_replayed"

    def __init__(
        self,
        *,
        session: Session,
        business_repository: BusinessRepository,
        principal_repository: PrincipalRepository,
        provider_connection_repository: ProviderConnectionRepository,
        provider_oauth_state_repository: ProviderOAuthStateRepository,
        oauth_client: GoogleOAuthWebClient,
        token_cipher: FernetTokenCipher,
        auth_audit_service: AuthAuditService,
        redirect_uri: str,
        state_ttl_seconds: int,
    ) -> None:
        normalized_redirect_uri = redirect_uri.strip()
        if not normalized_redirect_uri:
            raise GoogleBusinessProfileConnectionConfigurationError(
                "Google Business Profile redirect URI is not configured."
            )
        if state_ttl_seconds <= 0:
            raise GoogleBusinessProfileConnectionConfigurationError(
                "Google Business Profile state TTL must be positive."
            )

        self.session = session
        self.business_repository = business_repository
        self.principal_repository = principal_repository
        self.provider_connection_repository = provider_connection_repository
        self.provider_oauth_state_repository = provider_oauth_state_repository
        self.oauth_client = oauth_client
        self.token_cipher = token_cipher
        self.auth_audit_service = auth_audit_service
        self.redirect_uri = normalized_redirect_uri
        self.state_ttl_seconds = state_ttl_seconds

    def start_connection(
        self,
        *,
        business_id: str,
        principal_id: str,
    ) -> GoogleBusinessProfileConnectStartResult:
        self._ensure_business_and_active_principal(business_id=business_id, principal_id=principal_id)

        raw_state = secrets.token_urlsafe(32)
        expires_at = utc_now() + timedelta(seconds=self.state_ttl_seconds)
        oauth_state = ProviderOAuthState(
            id=str(uuid4()),
            provider=self.PROVIDER,
            business_id=business_id,
            principal_id=principal_id,
            state_hash=_hash_state(raw_state),
            expires_at=expires_at,
        )
        self.provider_oauth_state_repository.create(oauth_state)

        auth_url = self.build_auth_url(state=raw_state)
        self.auth_audit_service.record_event(
            business_id=business_id,
            actor_principal_id=principal_id,
            target_type=self.TARGET_TYPE,
            target_id=self.PROVIDER,
            event_type=self.EVENT_CONNECT_STARTED,
            details={
                "provider": self.PROVIDER,
                "scope": self.BUSINESS_PROFILE_SCOPE,
            },
        )
        self.session.commit()
        return GoogleBusinessProfileConnectStartResult(
            authorization_url=auth_url,
            state_expires_at=expires_at.isoformat(),
            provider=self.PROVIDER,
            required_scope=self.BUSINESS_PROFILE_SCOPE,
        )

    def build_auth_url(self, *, state: str) -> str:
        return self.oauth_client.build_auth_url(
            redirect_uri=self.redirect_uri,
            state=state,
            scopes=(self.BUSINESS_PROFILE_SCOPE,),
            access_type="offline",
            include_granted_scopes=True,
            prompt="consent",
        )

    def exchange_code_for_tokens(self, *, code: str) -> GoogleOAuthTokenResponse:
        return self.oauth_client.exchange_code_for_tokens(
            code=code,
            redirect_uri=self.redirect_uri,
        )

    def handle_callback(
        self,
        *,
        state: str | None,
        code: str | None,
        error: str | None,
        error_description: str | None,
    ) -> GoogleBusinessProfileConnectionStatusResult:
        normalized_state = (state or "").strip()
        if not normalized_state:
            raise GoogleBusinessProfileConnectionValidationError("OAuth state is required.", status_code=400)

        oauth_state = self.provider_oauth_state_repository.get_active_by_state_hash(
            provider=self.PROVIDER,
            state_hash=_hash_state(normalized_state),
        )
        if oauth_state is None:
            raise GoogleBusinessProfileConnectionValidationError(
                "OAuth state is invalid or expired.",
                status_code=401,
            )

        principal = self.principal_repository.get_for_business(
            oauth_state.business_id,
            oauth_state.principal_id,
        )
        self.provider_oauth_state_repository.mark_consumed(oauth_state)
        if principal is None or not principal.is_active:
            self.auth_audit_service.record_event(
                business_id=oauth_state.business_id,
                actor_principal_id=oauth_state.principal_id,
                target_type=self.TARGET_TYPE,
                target_id=self.PROVIDER,
                event_type=self.EVENT_CALLBACK_REPLAYED,
                details={
                    "provider": self.PROVIDER,
                    "reason": "principal_inactive_or_missing",
                },
            )
            self.session.commit()
            raise GoogleBusinessProfileConnectionValidationError(
                "Principal is inactive or missing for OAuth callback.",
                status_code=403,
            )

        normalized_error = (error or "").strip()
        normalized_error_description = (error_description or "").strip()
        if normalized_error:
            event_type = self.EVENT_CONNECT_DENIED if normalized_error == "access_denied" else self.EVENT_CONNECT_FAILED
            self.auth_audit_service.record_event(
                business_id=oauth_state.business_id,
                actor_principal_id=oauth_state.principal_id,
                target_type=self.TARGET_TYPE,
                target_id=self.PROVIDER,
                event_type=event_type,
                details={
                    "provider": self.PROVIDER,
                    "error": normalized_error,
                    "error_description": normalized_error_description or None,
                },
            )
            self.session.commit()
            if normalized_error == "access_denied":
                raise GoogleBusinessProfileConnectionValidationError(
                    "Google Business Profile authorization was denied.",
                    status_code=400,
                )
            raise GoogleBusinessProfileConnectionValidationError(
                "Google Business Profile authorization failed.",
                status_code=400,
            )

        normalized_code = (code or "").strip()
        if not normalized_code:
            self.auth_audit_service.record_event(
                business_id=oauth_state.business_id,
                actor_principal_id=oauth_state.principal_id,
                target_type=self.TARGET_TYPE,
                target_id=self.PROVIDER,
                event_type=self.EVENT_CONNECT_FAILED,
                details={
                    "provider": self.PROVIDER,
                    "error": "missing_authorization_code",
                },
            )
            self.session.commit()
            raise GoogleBusinessProfileConnectionValidationError(
                "Google authorization code is required.",
                status_code=400,
            )

        try:
            tokens = self.exchange_code_for_tokens(code=normalized_code)
        except GoogleOAuthError as exc:
            self.auth_audit_service.record_event(
                business_id=oauth_state.business_id,
                actor_principal_id=oauth_state.principal_id,
                target_type=self.TARGET_TYPE,
                target_id=self.PROVIDER,
                event_type=self.EVENT_CONNECT_FAILED,
                details={
                    "provider": self.PROVIDER,
                    "error": "token_exchange_failed",
                    "message": str(exc),
                },
            )
            self.session.commit()
            raise GoogleBusinessProfileConnectionValidationError(
                "Google token exchange failed.",
                status_code=400,
            ) from exc

        normalized_scopes = self._normalize_scopes(tokens.scope)
        if self.BUSINESS_PROFILE_SCOPE not in normalized_scopes:
            self.auth_audit_service.record_event(
                business_id=oauth_state.business_id,
                actor_principal_id=oauth_state.principal_id,
                target_type=self.TARGET_TYPE,
                target_id=self.PROVIDER,
                event_type=self.EVENT_CONNECT_FAILED,
                details={
                    "provider": self.PROVIDER,
                    "error": "missing_scope",
                    "required_scope": self.BUSINESS_PROFILE_SCOPE,
                    "granted_scopes": list(normalized_scopes),
                },
            )
            self.session.commit()
            raise GoogleBusinessProfileConnectionValidationError(
                "Google Business Profile scope was not granted.",
                status_code=422,
            )

        existing = self.provider_connection_repository.get_for_business_provider(
            business_id=oauth_state.business_id,
            provider=self.PROVIDER,
        )
        try:
            access_token_encrypted = self.token_cipher.encrypt(tokens.access_token)
        except TokenCipherError as exc:
            raise GoogleBusinessProfileConnectionConfigurationError(
                "Unable to encrypt Google provider tokens."
            ) from exc

        refresh_token_encrypted = existing.refresh_token_encrypted if existing is not None else None
        if tokens.refresh_token:
            try:
                refresh_token_encrypted = self.token_cipher.encrypt(tokens.refresh_token)
            except TokenCipherError as exc:
                raise GoogleBusinessProfileConnectionConfigurationError(
                    "Unable to encrypt Google provider refresh token."
                ) from exc

        if not refresh_token_encrypted:
            self.auth_audit_service.record_event(
                business_id=oauth_state.business_id,
                actor_principal_id=oauth_state.principal_id,
                target_type=self.TARGET_TYPE,
                target_id=self.PROVIDER,
                event_type=self.EVENT_CONNECT_FAILED,
                details={
                    "provider": self.PROVIDER,
                    "error": "missing_refresh_token",
                },
            )
            self.session.commit()
            raise GoogleBusinessProfileConnectionValidationError(
                (
                    "Google did not return a refresh token. Disconnect and reconnect with consent "
                    "to grant offline access."
                ),
                status_code=422,
            )

        expires_at = None
        if tokens.expires_in is not None:
            expires_at = utc_now() + timedelta(seconds=tokens.expires_in)

        if existing is None:
            connection = ProviderConnection(
                id=str(uuid4()),
                provider=self.PROVIDER,
                business_id=oauth_state.business_id,
                principal_id=oauth_state.principal_id,
                granted_scopes=" ".join(normalized_scopes),
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                access_token_expires_at=expires_at,
                external_subject=tokens.id_token_subject,
                external_account_email=tokens.id_token_email,
                is_active=True,
                last_error=None,
                connected_at=utc_now(),
                disconnected_at=None,
            )
            self.provider_connection_repository.create(connection)
        else:
            existing.principal_id = oauth_state.principal_id
            existing.granted_scopes = " ".join(normalized_scopes)
            existing.access_token_encrypted = access_token_encrypted
            existing.refresh_token_encrypted = refresh_token_encrypted
            existing.access_token_expires_at = expires_at
            if tokens.id_token_subject:
                existing.external_subject = tokens.id_token_subject
            if tokens.id_token_email:
                existing.external_account_email = tokens.id_token_email
            existing.is_active = True
            existing.last_error = None
            existing.connected_at = utc_now()
            existing.disconnected_at = None
            connection = self.provider_connection_repository.save(existing)

        self.auth_audit_service.record_event(
            business_id=oauth_state.business_id,
            actor_principal_id=oauth_state.principal_id,
            target_type=self.TARGET_TYPE,
            target_id=self.PROVIDER,
            event_type=self.EVENT_CONNECT_SUCCEEDED,
            details={
                "provider": self.PROVIDER,
                "granted_scopes": list(normalized_scopes),
                "principal_id": oauth_state.principal_id,
            },
        )
        self.session.commit()
        return self._status_from_connection(connection)

    def get_connection_status(
        self,
        *,
        business_id: str,
    ) -> GoogleBusinessProfileConnectionStatusResult:
        connection = self.provider_connection_repository.get_for_business_provider(
            business_id=business_id,
            provider=self.PROVIDER,
        )
        if connection is None or not connection.is_active:
            return GoogleBusinessProfileConnectionStatusResult(
                connected=False,
                provider=self.PROVIDER,
                business_id=business_id,
                principal_id=None,
                scopes=(),
                access_token_expires_at=None,
                connected_at=None,
                updated_at=None,
                last_error=connection.last_error if connection is not None else None,
            )
        return self._status_from_connection(connection)

    def refresh_access_token(
        self,
        *,
        business_id: str,
    ) -> GoogleBusinessProfileConnectionStatusResult:
        connection = self.provider_connection_repository.get_for_business_provider(
            business_id=business_id,
            provider=self.PROVIDER,
        )
        if connection is None or not connection.is_active:
            raise GoogleBusinessProfileConnectionNotFoundError("Google Business Profile connection not found.")
        if not connection.refresh_token_encrypted:
            raise GoogleBusinessProfileConnectionValidationError("Stored Google refresh token is missing.")

        try:
            refresh_token = self.token_cipher.decrypt(connection.refresh_token_encrypted)
        except TokenCipherError as exc:
            raise GoogleBusinessProfileConnectionConfigurationError(
                "Unable to decrypt stored Google refresh token."
            ) from exc

        try:
            refreshed = self.oauth_client.refresh_access_token(refresh_token=refresh_token)
        except GoogleOAuthError as exc:
            connection.last_error = str(exc)[:512]
            self.provider_connection_repository.save(connection)
            self.session.commit()
            raise GoogleBusinessProfileConnectionValidationError(
                "Google access token refresh failed.",
                status_code=401,
            ) from exc

        try:
            connection.access_token_encrypted = self.token_cipher.encrypt(refreshed.access_token)
            if refreshed.refresh_token:
                connection.refresh_token_encrypted = self.token_cipher.encrypt(refreshed.refresh_token)
        except TokenCipherError as exc:
            raise GoogleBusinessProfileConnectionConfigurationError(
                "Unable to encrypt refreshed Google provider tokens."
            ) from exc

        if refreshed.scope:
            connection.granted_scopes = " ".join(self._normalize_scopes(refreshed.scope))
        if refreshed.expires_in is not None:
            connection.access_token_expires_at = utc_now() + timedelta(seconds=refreshed.expires_in)
        connection.last_error = None
        self.provider_connection_repository.save(connection)
        self.session.commit()
        return self._status_from_connection(connection)

    def revoke_or_disconnect_provider(
        self,
        *,
        business_id: str,
        actor_principal_id: str,
    ) -> bool:
        connection = self.provider_connection_repository.get_for_business_provider(
            business_id=business_id,
            provider=self.PROVIDER,
        )
        if connection is None:
            return False

        token_to_revoke: str | None = None
        try:
            if connection.refresh_token_encrypted:
                token_to_revoke = self.token_cipher.decrypt(connection.refresh_token_encrypted)
            elif connection.access_token_encrypted:
                token_to_revoke = self.token_cipher.decrypt(connection.access_token_encrypted)
        except TokenCipherError:
            token_to_revoke = None

        revoked = False
        if token_to_revoke:
            revoked = self.oauth_client.revoke_token(token=token_to_revoke)

        connection.is_active = False
        connection.access_token_encrypted = None
        connection.refresh_token_encrypted = None
        connection.access_token_expires_at = None
        connection.disconnected_at = utc_now()
        connection.last_error = None if revoked else "Google token revoke was not confirmed."
        self.provider_connection_repository.save(connection)
        self.auth_audit_service.record_event(
            business_id=business_id,
            actor_principal_id=actor_principal_id,
            target_type=self.TARGET_TYPE,
            target_id=self.PROVIDER,
            event_type=self.EVENT_DISCONNECTED,
            details={
                "provider": self.PROVIDER,
                "revoked": revoked,
            },
        )
        self.session.commit()
        return True

    def _status_from_connection(
        self,
        connection: ProviderConnection,
    ) -> GoogleBusinessProfileConnectionStatusResult:
        scopes = tuple(scope for scope in connection.granted_scopes.split(" ") if scope)
        return GoogleBusinessProfileConnectionStatusResult(
            connected=bool(connection.is_active and connection.refresh_token_encrypted),
            provider=connection.provider,
            business_id=connection.business_id,
            principal_id=connection.principal_id,
            scopes=scopes,
            access_token_expires_at=(
                connection.access_token_expires_at.isoformat() if connection.access_token_expires_at else None
            ),
            connected_at=connection.connected_at.isoformat() if connection.connected_at else None,
            updated_at=connection.updated_at.isoformat() if connection.updated_at else None,
            last_error=connection.last_error,
        )

    def _ensure_business_and_active_principal(self, *, business_id: str, principal_id: str) -> None:
        business = self.business_repository.get(business_id)
        if business is None:
            raise GoogleBusinessProfileConnectionNotFoundError("Business not found.")

        principal = self.principal_repository.get_for_business(business_id, principal_id)
        if principal is None:
            raise GoogleBusinessProfileConnectionNotFoundError("Principal not found.")
        if not principal.is_active:
            raise GoogleBusinessProfileConnectionValidationError(
                "Principal is inactive.",
                status_code=403,
            )

    def _normalize_scopes(self, raw_scope: str | None) -> tuple[str, ...]:
        if not raw_scope:
            return ()
        unique = {scope.strip() for scope in raw_scope.split(" ") if scope.strip()}
        return tuple(sorted(unique))


def _hash_state(raw_state: str) -> str:
    return hashlib.sha256(raw_state.encode("utf-8")).hexdigest()
