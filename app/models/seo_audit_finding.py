from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class SEOAuditFinding(Base):
    __tablename__ = "seo_audit_findings"

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
    audit_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("seo_audit_runs.id"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("seo_audit_pages.id"),
        nullable=True,
        index=True,
    )
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    site = relationship("SEOSite")
    audit_run = relationship("SEOAuditRun")
    page = relationship("SEOAuditPage")
