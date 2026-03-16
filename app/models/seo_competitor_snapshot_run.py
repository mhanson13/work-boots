from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class SEOCompetitorSnapshotRun(Base):
    __tablename__ = "seo_competitor_snapshot_runs"
    __table_args__ = (
        Index(
            "ix_seo_competitor_snapshot_runs_business_set_created_at",
            "business_id",
            "competitor_set_id",
            "created_at",
        ),
        Index("ix_seo_competitor_snapshot_runs_business_status", "business_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    business_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )
    site_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_sites.id"),
        nullable=False,
        index=True,
    )
    competitor_set_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_competitor_sets.id"),
        nullable=False,
        index=True,
    )
    client_audit_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_audit_runs.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    max_domains: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    max_pages_per_domain: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    same_domain_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    domains_targeted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    domains_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_captured: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_encountered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_principal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    competitor_set = relationship("SEOCompetitorSet")
    site = relationship("SEOSite")
