from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4
import logging

from sqlalchemy.orm import Session

from app.integrations.seo_summary_provider import SEOAuditSummaryProvider
from app.models.seo_audit_summary import SEOAuditSummary
from app.repositories.business_repository import BusinessRepository
from app.repositories.seo_audit_repository import SEOAuditRepository
from app.repositories.seo_audit_summary_repository import SEOAuditSummaryRepository


logger = logging.getLogger(__name__)


class SEOSummaryNotFoundError(ValueError):
    pass


class SEOSummaryValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SEOSummaryResult:
    summary: SEOAuditSummary


class SEOSummaryService:
    def __init__(
        self,
        *,
        session: Session,
        business_repository: BusinessRepository,
        seo_audit_repository: SEOAuditRepository,
        seo_audit_summary_repository: SEOAuditSummaryRepository,
        provider: SEOAuditSummaryProvider,
    ) -> None:
        self.session = session
        self.business_repository = business_repository
        self.seo_audit_repository = seo_audit_repository
        self.seo_audit_summary_repository = seo_audit_summary_repository
        self.provider = provider

    def summarize_run(
        self,
        *,
        business_id: str,
        run_id: str,
        created_by_principal_id: str | None,
    ) -> SEOSummaryResult:
        business = self.business_repository.get(business_id)
        if business is None:
            raise SEOSummaryNotFoundError("Business not found")

        run = self.seo_audit_repository.get_run_for_business(business_id, run_id)
        if run is None:
            raise SEOSummaryNotFoundError("SEO audit run not found")
        if run.status != "completed":
            raise SEOSummaryValidationError("SEO audit run must be completed before summarization")

        findings = self.seo_audit_repository.list_findings_for_business_run(business_id, run_id)
        version = self.seo_audit_summary_repository.next_version(business_id, run_id)

        try:
            output = self.provider.generate_summary(run=run, findings=findings)
            summary = SEOAuditSummary(
                id=str(uuid4()),
                business_id=business_id,
                site_id=run.site_id,
                audit_run_id=run.id,
                version=version,
                status="completed",
                overall_health_summary=output.overall_health_summary,
                top_issues_json=output.top_issues,
                top_priorities_json=output.top_priorities,
                plain_english_explanation=output.plain_english_explanation,
                model_name=output.model_name,
                prompt_version=output.prompt_version,
                error_summary=None,
                created_by_principal_id=created_by_principal_id,
            )
            self.seo_audit_summary_repository.create(summary)
            self.session.commit()
            self.session.refresh(summary)
            return SEOSummaryResult(summary=summary)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "SEO summary generation failed business_id=%s audit_run_id=%s reason=%s",
                business_id,
                run_id,
                str(exc),
            )
            failed = SEOAuditSummary(
                id=str(uuid4()),
                business_id=business_id,
                site_id=run.site_id,
                audit_run_id=run.id,
                version=version,
                status="failed",
                overall_health_summary=None,
                top_issues_json=[],
                top_priorities_json=[],
                plain_english_explanation=None,
                model_name="summary-provider-error",
                prompt_version="seo-summary-v1",
                error_summary=str(exc),
                created_by_principal_id=created_by_principal_id,
            )
            self.seo_audit_summary_repository.create(failed)
            self.session.commit()
            raise SEOSummaryValidationError("Summary generation failed") from exc
