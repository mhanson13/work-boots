from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class SEORecommendation(Base):
    __tablename__ = "seo_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "recommendation_run_id",
            "rule_key",
            name="uq_seo_recommendations_business_run_rule_key",
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'accepted', 'dismissed', 'snoozed', 'resolved')",
            name="ck_seo_recommendations_status",
        ),
        CheckConstraint(
            "decision IS NULL OR decision IN ('accept', 'dismiss', 'snooze', 'resolve', 'reopen', 'start')",
            name="ck_seo_recommendations_decision",
        ),
        CheckConstraint(
            "priority_band IN ('low', 'medium', 'high', 'critical')",
            name="ck_seo_recommendations_priority_band",
        ),
        ForeignKeyConstraint(
            ["business_id", "assigned_principal_id"],
            ["principals.business_id", "principals.id"],
            name="fk_seo_recommendations_business_assigned_principal",
        ),
        Index(
            "ix_seo_recommendations_business_site_created_at",
            "business_id",
            "site_id",
            "created_at",
        ),
        Index(
            "ix_seo_recommendations_business_run_priority",
            "business_id",
            "recommendation_run_id",
            "priority_score",
        ),
        Index("ix_seo_recommendations_business_severity", "business_id", "severity"),
        Index("ix_seo_recommendations_business_category", "business_id", "category"),
        Index("ix_seo_recommendations_business_effort", "business_id", "effort_bucket"),
        Index(
            "ix_seo_recommendations_business_site_status_priority",
            "business_id",
            "site_id",
            "status",
            "priority_score",
        ),
        Index("ix_seo_recommendations_business_priority_band", "business_id", "priority_band"),
        Index("ix_seo_recommendations_business_assigned_principal", "business_id", "assigned_principal_id"),
        Index("ix_seo_recommendations_business_due_at", "business_id", "due_at"),
        Index("ix_seo_recommendations_business_snoozed_until", "business_id", "snoozed_until"),
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
    recommendation_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_recommendation_runs.id"),
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
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    priority_band: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", index=True)
    effort_bucket: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM", index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_principal_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by_principal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    recommendation_run = relationship("SEORecommendationRun")
    site = relationship("SEOSite")
    audit_run = relationship("SEOAuditRun")
    comparison_run = relationship("SEOCompetitorComparisonRun")
