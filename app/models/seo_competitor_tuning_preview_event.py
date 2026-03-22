from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class SEOCompetitorTuningPreviewEvent(Base):
    __tablename__ = "seo_competitor_tuning_preview_events"
    __table_args__ = (
        Index(
            "ix_sctpe_biz_site_created",
            "business_id",
            "site_id",
            "created_at",
        ),
        Index(
            "ix_sctpe_biz_site_applied",
            "business_id",
            "site_id",
            "applied_at",
        ),
        Index(
            "ix_sctpe_biz_site_eval",
            "business_id",
            "site_id",
            "evaluated_at",
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
    source_narrative_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_recommendation_narratives.id"),
        nullable=True,
    )
    source_recommendation_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_recommendation_runs.id"),
        nullable=True,
    )
    preview_request: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    preview_response: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluated_generation_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_competitor_profile_generation_runs.id"),
        nullable=True,
    )
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_included_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_included_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_margin: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direction_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
