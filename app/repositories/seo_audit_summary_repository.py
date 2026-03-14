from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.seo_audit_summary import SEOAuditSummary


class SEOAuditSummaryRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, summary: SEOAuditSummary) -> SEOAuditSummary:
        self.session.add(summary)
        self.session.flush()
        return summary

    def list_for_business_run(self, business_id: str, run_id: str) -> list[SEOAuditSummary]:
        stmt: Select[tuple[SEOAuditSummary]] = (
            select(SEOAuditSummary)
            .where(SEOAuditSummary.business_id == business_id)
            .where(SEOAuditSummary.audit_run_id == run_id)
            .order_by(SEOAuditSummary.version.asc(), SEOAuditSummary.created_at.asc())
        )
        return list(self.session.scalars(stmt))

    def next_version(self, business_id: str, run_id: str) -> int:
        stmt = (
            select(func.max(SEOAuditSummary.version))
            .where(SEOAuditSummary.business_id == business_id)
            .where(SEOAuditSummary.audit_run_id == run_id)
        )
        max_version = self.session.scalar(stmt)
        return int(max_version or 0) + 1
