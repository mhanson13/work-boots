from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_seo_automation_job,
    get_seo_competitor_profile_generation_retention_job,
    get_lead_reminder_job,
    get_tenant_context,
    resolve_tenant_business_id,
    TenantContext,
)
from app.jobs.lead_reminders import LeadReminderJob
from app.jobs.seo_competitor_profile_generation_retention import SEOCompetitorProfileGenerationRetentionJob
from app.jobs.seo_automation import SEOAutomationJob
from app.schemas.lead import ReminderRunActionRead, ReminderRunRequest, ReminderRunResponse
from app.schemas.seo_automation import SEOAutomationDueRunRequest, SEOAutomationDueRunSummaryRead
from app.schemas.seo_competitor import (
    SEOCompetitorProfileGenerationRetentionCleanupRead,
    SEOCompetitorProfileGenerationRetentionCleanupRequest,
)
from app.services.seo_competitor_profile_generation import (
    SEOCompetitorProfileGenerationNotFoundError,
    SEOCompetitorProfileGenerationValidationError,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/lead-reminders/run", response_model=ReminderRunResponse, status_code=status.HTTP_200_OK)
def run_lead_reminders(
    payload: ReminderRunRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    reminder_job: LeadReminderJob = Depends(get_lead_reminder_job),
) -> ReminderRunResponse:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=payload.business_id,
    )
    try:
        result = reminder_job.run(business_id=scoped_business_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ReminderRunResponse(
        business_id=result.business_id,
        scanned_leads=result.scanned_leads,
        reminders_sent=result.reminders_sent,
        reminder_15m_sent=result.reminder_15m_sent,
        reminder_2h_sent=result.reminder_2h_sent,
        actions=[ReminderRunActionRead(**action.__dict__) for action in result.actions],
    )


@router.post("/seo-automation/run-due", response_model=SEOAutomationDueRunSummaryRead, status_code=status.HTTP_200_OK)
def run_due_seo_automation(
    payload: SEOAutomationDueRunRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    automation_job: SEOAutomationJob = Depends(get_seo_automation_job),
) -> SEOAutomationDueRunSummaryRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=payload.business_id,
    )
    try:
        result = automation_job.run_due(limit=payload.limit, business_id=scoped_business_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SEOAutomationDueRunSummaryRead(
        scanned_configs=result.scanned_configs,
        triggered_runs=result.triggered_runs,
        skipped_active_runs=result.skipped_active_runs,
        failed_triggers=result.failed_triggers,
    )


@router.post(
    "/seo-competitor-profile-generation/cleanup",
    response_model=SEOCompetitorProfileGenerationRetentionCleanupRead,
    status_code=status.HTTP_200_OK,
)
def cleanup_seo_competitor_profile_generation_retention(
    payload: SEOCompetitorProfileGenerationRetentionCleanupRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    cleanup_job: SEOCompetitorProfileGenerationRetentionJob = Depends(
        get_seo_competitor_profile_generation_retention_job
    ),
) -> SEOCompetitorProfileGenerationRetentionCleanupRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=payload.business_id,
    )
    try:
        summary = cleanup_job.run_cleanup(
            business_id=scoped_business_id,
            site_id=payload.site_id,
        )
    except SEOCompetitorProfileGenerationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SEOCompetitorProfileGenerationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    return SEOCompetitorProfileGenerationRetentionCleanupRead(
        business_id=scoped_business_id,
        site_id=payload.site_id,
        stale_runs_reconciled=summary.stale_runs_reconciled,
        raw_output_pruned_runs=summary.raw_output_pruned_runs,
        rejected_drafts_pruned=summary.rejected_drafts_pruned,
        runs_pruned=summary.runs_pruned,
    )
