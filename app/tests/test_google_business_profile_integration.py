from __future__ import annotations

import hashlib
from urllib.parse import parse_qs, urlencode, urlparse
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import (
    TenantContext,
    get_authenticated_principal,
    get_db,
    get_google_oauth_client,
    get_google_oidc_verifier,
    get_tenant_context,
)
from app.api.routes.auth import router as auth_router
from app.api.routes.integrations import router as integrations_router
from app.core.config import get_settings
from app.core.token_cipher import FernetTokenCipher
from app.integrations.google_auth import GoogleIdentityClaims, GoogleOIDCVerificationError
from app.integrations.google_oauth import GoogleOAuthError, GoogleOAuthTokenResponse
from app.models.auth_audit_event import AuthAuditEvent
from app.models.business import Business
from app.models.principal import Principal, PrincipalRole
from app.models.principal_identity import PrincipalIdentity
from app.models.provider_connection import ProviderConnection
from app.models.provider_oauth_state import ProviderOAuthState


class _StubGoogleOAuthClient:
    def __init__(self) -> None:
        self.exchange_map: dict[str, GoogleOAuthTokenResponse | Exception] = {}
        self.exchange_calls: list[tuple[str, str]] = []
        self.build_calls: list[dict[str, object]] = []
        self.refresh_map: dict[str, GoogleOAuthTokenResponse | Exception] = {}
        self.revoke_calls: list[str] = []
        self.revoke_result = True

    def build_auth_url(
        self,
        *,
        redirect_uri: str,
        state: str,
        scopes: tuple[str, ...],
        access_type: str = "offline",
        include_granted_scopes: bool = True,
        prompt: str = "consent",
    ) -> str:
        self.build_calls.append(
            {
                "redirect_uri": redirect_uri,
                "state": state,
                "scopes": scopes,
                "access_type": access_type,
                "include_granted_scopes": include_granted_scopes,
                "prompt": prompt,
            }
        )
        query = urlencode(
            {
                "client_id": "google-oauth-client-id.apps.googleusercontent.com",
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(scopes),
                "state": state,
                "access_type": access_type,
                "include_granted_scopes": "true" if include_granted_scopes else "false",
                "prompt": prompt,
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    def exchange_code_for_tokens(
        self,
        *,
        code: str,
        redirect_uri: str,
    ) -> GoogleOAuthTokenResponse:
        self.exchange_calls.append((code, redirect_uri))
        result = self.exchange_map.get(code)
        if result is None:
            raise GoogleOAuthError("authorization code is unknown for test stub")
        if isinstance(result, Exception):
            raise result
        return result

    def refresh_access_token(self, *, refresh_token: str) -> GoogleOAuthTokenResponse:
        result = self.refresh_map.get(refresh_token)
        if result is None:
            raise GoogleOAuthError("refresh token is unknown for test stub")
        if isinstance(result, Exception):
            raise result
        return result

    def revoke_token(self, *, token: str) -> bool:
        self.revoke_calls.append(token)
        return self.revoke_result


class _StubGoogleVerifier:
    def __init__(self, mapping: dict[str, GoogleIdentityClaims]) -> None:
        self.mapping = mapping

    def verify_id_token(self, id_token: str) -> GoogleIdentityClaims:
        claims = self.mapping.get(id_token)
        if claims is None:
            raise GoogleOIDCVerificationError("Google token verification failed.")
        return claims


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _set_auth_env(monkeypatch: pytest.MonkeyPatch, *, default_business_id: str) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEFAULT_BUSINESS_ID", default_business_id)
    monkeypatch.setenv("API_TOKEN_HASH_PEPPER", "test-pepper")
    monkeypatch.setenv("GOOGLE_AUTH_ENABLED", "true")
    monkeypatch.setenv("GOOGLE_OIDC_CLIENT_ID", "google-client-id")
    monkeypatch.setenv("GOOGLE_OIDC_REQUIRE_EMAIL_VERIFIED", "true")
    monkeypatch.setenv("APP_SESSION_SECRET", "app-session-secret")
    monkeypatch.setenv("APP_SESSION_TTL_SECONDS", "3600")
    monkeypatch.setenv("APP_SESSION_REFRESH_TTL_SECONDS", "86400")
    monkeypatch.setenv("SESSION_STATE_BACKEND", "inmemory")
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "inmemory")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "google-oauth-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "google-oauth-client-secret")
    monkeypatch.setenv(
        "GOOGLE_BUSINESS_PROFILE_REDIRECT_URI",
        "https://operator.workboots.example/api/integrations/google/business-profile/connect/callback",
    )
    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN_ENCRYPTION_SECRET", "gbp-token-encryption-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_TOKEN_ENCRYPTION_KEY_VERSION", "v1")
    monkeypatch.setenv("GOOGLE_BUSINESS_PROFILE_STATE_TTL_SECONDS", "600")


def _seed_principal(
    db_session,
    *,
    business_id: str,
    principal_id: str,
    is_active: bool = True,
) -> Principal:
    principal = Principal(
        business_id=business_id,
        id=principal_id,
        display_name=principal_id,
        role=PrincipalRole.ADMIN,
        is_active=is_active,
    )
    db_session.add(principal)
    db_session.commit()
    return principal


def _make_integrations_client(
    db_session,
    *,
    oauth_client: _StubGoogleOAuthClient,
    business_id: str,
    principal_id: str,
) -> TestClient:
    app = FastAPI()
    app.include_router(integrations_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_tenant_context() -> TenantContext:
        return TenantContext(
            business_id=business_id,
            principal_id=principal_id,
            auth_source="test_suite",
            principal_role=PrincipalRole.ADMIN,
        )

    def override_principal() -> Principal:
        principal = db_session.get(Principal, (business_id, principal_id))
        if principal is None:
            raise RuntimeError("principal fixture missing")
        return principal

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_google_oauth_client] = lambda: oauth_client
    app.dependency_overrides[get_tenant_context] = override_tenant_context
    app.dependency_overrides[get_authenticated_principal] = override_principal
    return TestClient(app)


def _make_auth_client(db_session, *, verifier: _StubGoogleVerifier) -> TestClient:
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(integrations_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_google_oidc_verifier] = lambda: verifier
    return TestClient(app)


def _start_connect(client: TestClient) -> dict[str, object]:
    response = client.post("/api/integrations/google/business-profile/connect/start")
    assert response.status_code == 200, response.text
    return response.json()


def _extract_state(authorization_url: str) -> str:
    parsed = urlparse(authorization_url)
    query = parse_qs(parsed.query)
    values = query.get("state", [])
    assert values
    return values[0]


def _provider_connection_for_business(db_session, business_id: str) -> ProviderConnection | None:
    return (
        db_session.query(ProviderConnection)
        .filter(ProviderConnection.business_id == business_id)
        .filter(ProviderConnection.provider == "google_business_profile")
        .one_or_none()
    )


def _seed_google_identity_mapping(
    db_session,
    *,
    business_id: str,
    principal_id: str,
    provider_subject: str,
) -> PrincipalIdentity:
    identity = PrincipalIdentity(
        id=str(uuid4()),
        provider="google",
        provider_subject=provider_subject,
        business_id=business_id,
        principal_id=principal_id,
        email="admin@workboots.example",
        email_verified=True,
        is_active=True,
    )
    db_session.add(identity)
    db_session.commit()
    return identity


def test_google_business_profile_connect_start_builds_expected_authorization_request(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-connect")
    oauth_client = _StubGoogleOAuthClient()
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-connect",
    )

    payload = _start_connect(client)
    assert payload["provider"] == "google_business_profile"
    assert payload["required_scope"] == "https://www.googleapis.com/auth/business.manage"

    authorization_url = str(payload["authorization_url"])
    parsed = urlparse(authorization_url)
    query = parse_qs(parsed.query)
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["https://www.googleapis.com/auth/business.manage"]
    assert query["access_type"] == ["offline"]
    assert query["include_granted_scopes"] == ["true"]
    assert query["prompt"] == ["consent"]
    assert query["redirect_uri"] == [
        "https://operator.workboots.example/api/integrations/google/business-profile/connect/callback"
    ]

    raw_state = query["state"][0]
    state_row = db_session.query(ProviderOAuthState).one()
    assert state_row.provider == "google_business_profile"
    assert state_row.state_hash == hashlib.sha256(raw_state.encode("utf-8")).hexdigest()
    assert state_row.consumed_at is None


def test_google_business_profile_callback_rejects_invalid_state(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-invalid-state")
    client = _make_integrations_client(
        db_session,
        oauth_client=_StubGoogleOAuthClient(),
        business_id=seeded_business.id,
        principal_id="admin-invalid-state",
    )

    response = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": "invalid-state", "code": "auth-code"},
    )
    assert response.status_code == 401
    assert "invalid or expired" in response.json()["detail"].lower()


def test_google_business_profile_callback_denied_consent(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-denied")
    client = _make_integrations_client(
        db_session,
        oauth_client=_StubGoogleOAuthClient(),
        business_id=seeded_business.id,
        principal_id="admin-denied",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={
            "state": state,
            "error": "access_denied",
            "error_description": "The user denied access",
        },
    )
    assert callback.status_code == 400
    assert "denied" in callback.json()["detail"].lower()

    state_row = db_session.query(ProviderOAuthState).one()
    assert state_row.consumed_at is not None
    denied_events = (
        db_session.query(AuthAuditEvent)
        .filter(AuthAuditEvent.business_id == seeded_business.id)
        .filter(AuthAuditEvent.event_type == "integration_google_business_profile_connect_denied")
        .all()
    )
    assert denied_events


def test_google_business_profile_callback_success_persists_encrypted_tokens(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-success")
    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["valid-code"] = GoogleOAuthTokenResponse(
        access_token="ya29.access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="1//refresh-token",
        scope="https://www.googleapis.com/auth/business.manage openid email",
        id_token_subject="google-subject-123",
        id_token_email="owner@workboots.example",
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-success",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "valid-code"},
    )
    assert callback.status_code == 200, callback.text
    payload = callback.json()
    assert payload["connected"] is True
    assert payload["provider"] == "google_business_profile"
    assert "https://www.googleapis.com/auth/business.manage" in payload["granted_scopes"]
    assert payload["refresh_token_present"] is True
    assert payload["reconnect_required"] is False

    row = _provider_connection_for_business(db_session, seeded_business.id)
    assert row is not None
    assert row.is_active is True
    assert row.created_by_principal_id == "admin-success"
    assert row.updated_by_principal_id == "admin-success"
    assert row.token_key_version == "v1"
    assert row.access_token_encrypted is not None
    assert row.refresh_token_encrypted is not None
    assert row.access_token_encrypted != "ya29.access-token"
    assert row.refresh_token_encrypted != "1//refresh-token"
    assert row.external_subject == "google-subject-123"
    assert row.external_account_email == "owner@workboots.example"

    cipher = FernetTokenCipher(secret="gbp-token-encryption-secret")
    assert cipher.decrypt(row.access_token_encrypted) == "ya29.access-token"
    assert cipher.decrypt(row.refresh_token_encrypted) == "1//refresh-token"


def test_google_business_profile_connection_status_contract_is_stable(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-status")
    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["status-code"] = GoogleOAuthTokenResponse(
        access_token="status-access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="status-refresh-token",
        scope="https://www.googleapis.com/auth/business.manage",
        id_token_subject=None,
        id_token_email=None,
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-status",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "status-code"},
    )
    assert callback.status_code == 200

    status_response = client.get("/api/integrations/google/business-profile/connection")
    assert status_response.status_code == 200
    payload = status_response.json()
    assert set(payload.keys()) == {
        "provider",
        "connected",
        "business_id",
        "granted_scopes",
        "refresh_token_present",
        "expires_at",
        "connected_at",
        "last_refreshed_at",
        "reconnect_required",
    }
    assert payload["provider"] == "google_business_profile"
    assert payload["connected"] is True
    assert payload["refresh_token_present"] is True
    assert payload["reconnect_required"] is False


def test_google_business_profile_callback_requires_refresh_token_for_initial_connection(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-no-refresh")
    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["code-no-refresh"] = GoogleOAuthTokenResponse(
        access_token="ya29.access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token=None,
        scope="https://www.googleapis.com/auth/business.manage",
        id_token_subject=None,
        id_token_email=None,
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-no-refresh",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "code-no-refresh"},
    )
    assert callback.status_code == 422
    detail = callback.json()["detail"]
    assert detail["reconnect_required"] is True
    assert "refresh token" in detail["message"].lower()
    assert _provider_connection_for_business(db_session, seeded_business.id) is None


def test_google_business_profile_callback_preserves_existing_refresh_token_when_not_reissued(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-refresh-preserve")
    cipher = FernetTokenCipher(secret="gbp-token-encryption-secret")
    existing = ProviderConnection(
        id=str(uuid4()),
        provider="google_business_profile",
        business_id=seeded_business.id,
        principal_id="admin-refresh-preserve",
        created_by_principal_id="admin-refresh-preserve",
        updated_by_principal_id="admin-refresh-preserve",
        granted_scopes="https://www.googleapis.com/auth/business.manage openid",
        token_key_version="v1",
        access_token_encrypted=cipher.encrypt("old-access-token"),
        refresh_token_encrypted=cipher.encrypt("existing-refresh-token"),
        is_active=True,
    )
    db_session.add(existing)
    db_session.commit()

    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["code-preserve-refresh"] = GoogleOAuthTokenResponse(
        access_token="new-access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token=None,
        scope=None,
        id_token_subject="google-subject-keep-refresh",
        id_token_email="refresh-preserve@workboots.example",
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-refresh-preserve",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "code-preserve-refresh"},
    )
    assert callback.status_code == 200
    payload = callback.json()
    assert payload["connected"] is True
    assert payload["refresh_token_present"] is True
    assert payload["reconnect_required"] is False

    db_session.expire_all()
    row = _provider_connection_for_business(db_session, seeded_business.id)
    assert row is not None
    assert cipher.decrypt(row.access_token_encrypted or "") == "new-access-token"
    assert cipher.decrypt(row.refresh_token_encrypted or "") == "existing-refresh-token"


def test_google_business_profile_callback_state_is_single_use(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-replay")
    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["replay-code"] = GoogleOAuthTokenResponse(
        access_token="ya29.access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="1//refresh-token",
        scope="https://www.googleapis.com/auth/business.manage",
        id_token_subject=None,
        id_token_email=None,
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-replay",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    first = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "replay-code"},
    )
    assert first.status_code == 200

    second = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "replay-code"},
    )
    assert second.status_code == 401
    assert "invalid or expired" in second.json()["detail"].lower()


def test_google_business_profile_disconnect_clears_tokens_and_revokes(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-disconnect")
    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["disconnect-code"] = GoogleOAuthTokenResponse(
        access_token="ya29.access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="1//refresh-token",
        scope="https://www.googleapis.com/auth/business.manage",
        id_token_subject=None,
        id_token_email=None,
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-disconnect",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "disconnect-code"},
    )
    assert callback.status_code == 200

    disconnect = client.post("/api/integrations/google/business-profile/disconnect")
    assert disconnect.status_code == 200
    payload = disconnect.json()
    assert payload["status"] == "disconnected"
    assert payload["connection"]["connected"] is False
    assert payload["connection"]["refresh_token_present"] is False

    row = _provider_connection_for_business(db_session, seeded_business.id)
    assert row is not None
    assert row.is_active is False
    assert row.access_token_encrypted is None
    assert row.refresh_token_encrypted is None
    assert row.disconnected_at is not None
    assert row.updated_by_principal_id == "admin-disconnect"
    assert oauth_client.revoke_calls == ["1//refresh-token"]


def test_google_business_profile_disconnect_tombstones_even_if_revoke_not_confirmed(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="admin-disconnect-no-revoke")
    oauth_client = _StubGoogleOAuthClient()
    oauth_client.revoke_result = False
    oauth_client.exchange_map["disconnect-code-no-revoke"] = GoogleOAuthTokenResponse(
        access_token="ya29.access-token",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="1//refresh-token",
        scope="https://www.googleapis.com/auth/business.manage",
        id_token_subject=None,
        id_token_email=None,
    )
    client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="admin-disconnect-no-revoke",
    )

    start_payload = _start_connect(client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "disconnect-code-no-revoke"},
    )
    assert callback.status_code == 200

    disconnect = client.post("/api/integrations/google/business-profile/disconnect")
    assert disconnect.status_code == 200

    row = _provider_connection_for_business(db_session, seeded_business.id)
    assert row is not None
    assert row.is_active is False
    assert row.access_token_encrypted is None
    assert row.refresh_token_encrypted is None
    assert row.last_error is not None
    assert "revoke" in row.last_error.lower()


def test_google_business_profile_connection_isolated_by_business_scope(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="tenant-a-admin")
    other_business = Business(
        id=str(uuid4()),
        name="Other Business",
        notification_phone="+13035559999",
        notification_email="owner@other.example",
        sms_enabled=True,
        email_enabled=True,
        customer_auto_ack_enabled=True,
        contractor_alerts_enabled=True,
    )
    db_session.add(other_business)
    db_session.commit()
    _seed_principal(db_session, business_id=other_business.id, principal_id="tenant-b-admin")

    oauth_client = _StubGoogleOAuthClient()
    oauth_client.exchange_map["tenant-a-code"] = GoogleOAuthTokenResponse(
        access_token="tenant-a-access",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="tenant-a-refresh",
        scope="https://www.googleapis.com/auth/business.manage",
        id_token_subject=None,
        id_token_email=None,
    )
    tenant_a_client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=seeded_business.id,
        principal_id="tenant-a-admin",
    )
    tenant_b_client = _make_integrations_client(
        db_session,
        oauth_client=oauth_client,
        business_id=other_business.id,
        principal_id="tenant-b-admin",
    )

    start_payload = _start_connect(tenant_a_client)
    state = _extract_state(str(start_payload["authorization_url"]))
    callback = tenant_a_client.get(
        "/api/integrations/google/business-profile/connect/callback",
        params={"state": state, "code": "tenant-a-code"},
    )
    assert callback.status_code == 200

    tenant_b_status = tenant_b_client.get("/api/integrations/google/business-profile/connection")
    assert tenant_b_status.status_code == 200
    assert tenant_b_status.json()["connected"] is False


def test_google_oidc_exchange_still_works_after_gbp_integration_wiring(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_auth_env(monkeypatch, default_business_id=seeded_business.id)
    _seed_principal(db_session, business_id=seeded_business.id, principal_id="oidc-admin")
    _seed_google_identity_mapping(
        db_session,
        business_id=seeded_business.id,
        principal_id="oidc-admin",
        provider_subject="google-sub-oidc",
    )
    verifier = _StubGoogleVerifier(
        {
            "valid-google-id-token": GoogleIdentityClaims(
                provider="google",
                subject="google-sub-oidc",
                email="oidc-admin@workboots.example",
                email_verified=True,
                issuer="https://accounts.google.com",
                audience="google-client-id",
                display_name="OIDC Admin",
            )
        }
    )
    client = _make_auth_client(db_session, verifier=verifier)

    exchange = client.post("/api/auth/google/exchange", json={"id_token": "valid-google-id-token"})
    assert exchange.status_code == 200
    payload = exchange.json()
    assert payload["token_type"] == "bearer"
    assert payload["principal"]["business_id"] == seeded_business.id
    assert payload["access_token"]
    assert payload["refresh_token"]
