from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.api.deps import (
    TenantContext,
    get_tenant_context,
    require_admin_rate_limit,
    require_credential_manager_principal,
)
from app.models.principal import Principal
from app.schemas.admin_logs import ADCRuntimeCheckResponse

router = APIRouter(prefix="/admin/runtime", tags=["admin-runtime"])
logger = logging.getLogger(__name__)
_CLOUD_LOGGING_READ_SCOPE = "https://www.googleapis.com/auth/logging.read"
_ADC_ERROR_MAX_CHARS = 256


def _load_google_auth():
    from google.auth import default as google_auth_default
    from google.auth.transport.requests import Request as GoogleAuthRequest

    return google_auth_default, GoogleAuthRequest


def _normalize_adc_error_message(error: Exception) -> str:
    normalized = " ".join(str(error or "").split())
    if not normalized:
        normalized = error.__class__.__name__
    if len(normalized) <= _ADC_ERROR_MAX_CHARS:
        return normalized
    return f"{normalized[: _ADC_ERROR_MAX_CHARS - 3]}..."


def _resolve_adc_runtime_status() -> ADCRuntimeCheckResponse:
    detected_project_id: str | None = None
    try:
        google_auth_default, google_auth_request_cls = _load_google_auth()
        credentials, detected_project_id = google_auth_default(scopes=[_CLOUD_LOGGING_READ_SCOPE])
        if credentials is None:
            raise RuntimeError("google.auth.default() did not return credentials.")
        credentials.refresh(google_auth_request_cls())
        if not str(getattr(credentials, "token", "") or "").strip():
            raise RuntimeError("ADC credentials did not return an access token.")

        logger.info(
            "admin_runtime_adc_check_success adc_available=true detected_project_id=%s",
            detected_project_id or "",
        )
        return ADCRuntimeCheckResponse(
            adc_available=True,
            project_id=(detected_project_id or None),
            error=None,
        )
    except Exception as exc:  # noqa: BLE001
        safe_error = _normalize_adc_error_message(exc)
        logger.warning(
            "admin_runtime_adc_check_failure adc_available=false detected_project_id=%s error=%s",
            detected_project_id or "",
            safe_error,
        )
        return ADCRuntimeCheckResponse(
            adc_available=False,
            project_id=(detected_project_id or None),
            error=safe_error,
        )


@router.get("/adc-check", response_model=ADCRuntimeCheckResponse)
def get_admin_runtime_adc_check(
    _: None = Depends(require_admin_rate_limit("runtime_adc_check")),
    __: Principal = Depends(require_credential_manager_principal),
    ___: TenantContext = Depends(get_tenant_context),
) -> ADCRuntimeCheckResponse:
    return _resolve_adc_runtime_status()
