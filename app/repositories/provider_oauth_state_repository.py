from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
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
