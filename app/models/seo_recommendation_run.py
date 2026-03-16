from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class SEORecommendationRun(Base):
    __tablename__ = "seo_recommendation_runs"
    __table_args__ = (
        CheckConstraint(
            "audit_run_id IS NOT NULL OR comparison_run_id IS NOT NULL",
            name="ck_seo_recommendation_runs_requires_input_lineage",
        ),
        Index(
            "ix_seo_recommendation_runs_business_site_created_at",
            "business_id",
            "site_id",
            "created_at",
        ),
        Index("ix_seo_recommendation_runs_business_status", "business_id", "status"),
        Index(
            "ix_seo_recommendation_runs_business_audit_run",
            "business_id",
            "audit_run_id",
        ),
        Index(
            "ix_seo_recommendation_runs_business_comparison_run",
            "business_id",
            "comparison_run_id",
        ),
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
    audit_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_audit_runs.id"),
        nullable=True,
        index=True,
    )
    comparison_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_competitor_comparison_runs.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    info_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_counts_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    effort_bucket_counts_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
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

    site = relationship("SEOSite")
    audit_run = relationship("SEOAuditRun")
    comparison_run = relationship("SEOCompetitorComparisonRun")
