from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class ProviderConnection(Base):
    __tablename__ = "provider_connections"
    __table_args__ = (
        ForeignKeyConstraint(
            ["business_id", "principal_id"],
            ["principals.business_id", "principals.id"],
            name="fk_provider_connections_business_id_principal_id_principals",
        ),
        UniqueConstraint(
            "provider",
            "business_id",
            name="uq_provider_connections_provider_business",
        ),
        Index(
            "ix_provider_connections_business_provider",
            "business_id",
            "provider",
        ),
        Index(
            "ix_provider_connections_business_principal",
            "business_id",
            "principal_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)
    principal_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_by_principal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_by_principal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    granted_scopes: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    token_key_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_account_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
