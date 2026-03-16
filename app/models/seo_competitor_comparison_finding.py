from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class SEOCompetitorComparisonFinding(Base):
    __tablename__ = "seo_competitor_comparison_findings"
    __table_args__ = (
        Index(
            "ix_seo_competitor_comparison_findings_business_run_created_at",
            "business_id",
            "comparison_run_id",
            "created_at",
        ),
        Index("ix_seo_competitor_comparison_findings_business_category", "business_id", "category"),
        Index("ix_seo_competitor_comparison_findings_business_severity", "business_id", "severity"),
        Index("ix_seo_competitor_comparison_findings_business_finding_type", "business_id", "finding_type"),
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
    comparison_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_competitor_comparison_runs.id"),
        nullable=False,
        index=True,
    )
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    client_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    gap_direction: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evidence_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    comparison_run = relationship("SEOCompetitorComparisonRun")
    competitor_set = relationship("SEOCompetitorSet")
    site = relationship("SEOSite")
