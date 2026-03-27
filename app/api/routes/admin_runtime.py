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
    credentials_class: str | None = None
    phase: str | None = None
    try:
        try:
            google_auth_default, google_auth_request_cls = _load_google_auth()
        except Exception as exc:  # noqa: BLE001
            phase = "dependency_missing"
            raise RuntimeError("google-auth transport dependency is unavailable.") from exc

        try:
            credentials, detected_project_id = google_auth_default(scopes=[_CLOUD_LOGGING_READ_SCOPE])
        except Exception as exc:  # noqa: BLE001
            phase = "adc_resolution_failure"
            raise RuntimeError("google.auth.default() failed to resolve credentials.") from exc

        if credentials is None:
            phase = "adc_resolution_failure"
            raise RuntimeError("google.auth.default() did not return credentials.")
        credentials_class = credentials.__class__.__name__
        try:
            credentials.refresh(google_auth_request_cls())
        except Exception as exc:  # noqa: BLE001
            phase = "token_refresh_failure"
            raise RuntimeError("ADC credentials failed refresh.") from exc

        if not str(getattr(credentials, "token", "") or "").strip():
            phase = "token_missing"
            raise RuntimeError("ADC credentials did not return an access token.")

        logger.info(
            "admin_runtime_adc_check_success adc_available=true detected_project_id=%s credentials_class=%s",
            detected_project_id or "",
            credentials_class or "",
        )
        return ADCRuntimeCheckResponse(
            adc_available=True,
            project_id=(detected_project_id or None),
            error=None,
            phase=None,
            cause_class=None,
            credentials_class=credentials_class,
        )
    except Exception as exc:  # noqa: BLE001
        root_error = exc.__cause__ if isinstance(exc.__cause__, Exception) else exc
        safe_error = _normalize_adc_error_message(root_error)
        cause_class = root_error.__class__.__name__
        resolved_phase = phase or "adc_authorization_failure"
        logger.warning(
            "admin_runtime_adc_check_failure adc_available=false detected_project_id=%s phase=%s cause_class=%s error=%s",
            detected_project_id or "",
            resolved_phase,
            cause_class,
            safe_error,
        )
        return ADCRuntimeCheckResponse(
            adc_available=False,
            project_id=(detected_project_id or None),
            error=safe_error,
            phase=resolved_phase,
            cause_class=cause_class,
            credentials_class=credentials_class,
        )


@router.get("/adc-check", response_model=ADCRuntimeCheckResponse)
def get_admin_runtime_adc_check(
    _: None = Depends(require_admin_rate_limit("runtime_adc_check")),
    __: Principal = Depends(require_credential_manager_principal),
    ___: TenantContext = Depends(get_tenant_context),
) -> ADCRuntimeCheckResponse:
    return _resolve_adc_runtime_status()
