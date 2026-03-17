from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select, update
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.provider_oauth_state import ProviderOAuthState


class ProviderOAuthStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, oauth_state: ProviderOAuthState) -> ProviderOAuthState:
        self.session.add(oauth_state)
        self.session.flush()
        return oauth_state

    def save(self, oauth_state: ProviderOAuthState) -> ProviderOAuthState:
        self.session.add(oauth_state)
        self.session.flush()
        return oauth_state

    def get_active_by_state_hash(
        self,
        *,
        provider: str,
        state_hash: str,
        as_of: datetime | None = None,
    ) -> ProviderOAuthState | None:
        timestamp = as_of or utc_now()
        stmt: Select[tuple[ProviderOAuthState]] = (
            select(ProviderOAuthState)
            .where(ProviderOAuthState.provider == provider)
            .where(ProviderOAuthState.state_hash == state_hash)
            .where(ProviderOAuthState.consumed_at.is_(None))
            .where(ProviderOAuthState.expires_at > timestamp)
        )
        return self.session.scalar(stmt)

    def mark_consumed(
        self,
        oauth_state: ProviderOAuthState,
        *,
        consumed_at: datetime | None = None,
    ) -> ProviderOAuthState:
        oauth_state.consumed_at = consumed_at or utc_now()
        self.session.add(oauth_state)
        self.session.flush()
        return oauth_state

    def mark_consumed_if_active(
        self,
        *,
        provider: str,
        oauth_state_id: str,
        as_of: datetime | None = None,
        consumed_at: datetime | None = None,
    ) -> bool:
        timestamp = as_of or utc_now()
        consumed_timestamp = consumed_at or timestamp
        stmt = (
            update(ProviderOAuthState)
            .where(ProviderOAuthState.id == oauth_state_id)
            .where(ProviderOAuthState.provider == provider)
            .where(ProviderOAuthState.consumed_at.is_(None))
            .where(ProviderOAuthState.expires_at > timestamp)
            .values(consumed_at=consumed_timestamp)
            .execution_options(synchronize_session=False)
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return bool(result.rowcount and result.rowcount > 0)
