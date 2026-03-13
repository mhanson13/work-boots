from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_email_intake_service, get_lead_intake_service
from app.schemas.lead import (
    EmailIntakeRequest,
    EmailIntakeResponse,
    LeadRead,
    ManualIntakeRequest,
    ManualIntakeResponse,
)
from app.services.email_intake import EmailIntakeService
from app.services.lead_intake import LeadIntakeService

router = APIRouter(prefix="/api/intake", tags=["intake"])


@router.post("/manual", response_model=ManualIntakeResponse, status_code=status.HTTP_201_CREATED)
def intake_manual(
    payload: ManualIntakeRequest,
    intake_service: LeadIntakeService = Depends(get_lead_intake_service),
) -> ManualIntakeResponse:
    try:
        lead = intake_service.create_manual_lead(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ManualIntakeResponse(
        lead=LeadRead.model_validate(lead),
        message="Lead captured from manual entry.",
    )


@router.post("/email", response_model=EmailIntakeResponse, status_code=status.HTTP_201_CREATED)
def intake_email(
    payload: EmailIntakeRequest,
    intake_service: EmailIntakeService = Depends(get_email_intake_service),
) -> EmailIntakeResponse:
    try:
        result = intake_service.ingest(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return EmailIntakeResponse(
        lead=LeadRead.model_validate(result.lead),
        duplicate=result.duplicate,
        parse_status=result.parse_status,
        events_recorded=result.events_recorded,
        message=result.message,
    )
