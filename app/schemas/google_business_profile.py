from __future__ import annotations

from pydantic import BaseModel, Field


class GoogleBusinessProfileConnectStartResponse(BaseModel):
    authorization_url: str = Field(min_length=1)
    state_expires_at: str
    provider: str
    required_scope: str


class GoogleBusinessProfileConnectionStatusResponse(BaseModel):
    connected: bool
    provider: str
    business_id: str
    principal_id: str | None
    scopes: list[str]
    access_token_expires_at: str | None
    connected_at: str | None
    updated_at: str | None
    last_error: str | None


class GoogleBusinessProfileDisconnectResponse(BaseModel):
    status: str
    connection: GoogleBusinessProfileConnectionStatusResponse
