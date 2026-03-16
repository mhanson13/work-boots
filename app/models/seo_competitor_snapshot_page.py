from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class SEOCompetitorSnapshotPage(Base):
    __tablename__ = "seo_competitor_snapshot_pages"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "snapshot_run_id",
            "competitor_domain_id",
            "url",
            name="uq_seo_competitor_snapshot_pages_business_run_domain_url",
        ),
        Index("ix_seo_competitor_snapshot_pages_business_run", "business_id", "snapshot_run_id"),
        Index("ix_seo_competitor_snapshot_pages_business_domain", "business_id", "competitor_domain_id"),
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
    snapshot_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_competitor_snapshot_runs.id"),
        nullable=False,
        index=True,
    )
    competitor_domain_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_competitor_domains.id"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    h1_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    h2_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    internal_link_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    competitor_set = relationship("SEOCompetitorSet")
    snapshot_run = relationship("SEOCompetitorSnapshotRun")
    competitor_domain = relationship("SEOCompetitorDomain")
    site = relationship("SEOSite")
