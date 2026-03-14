from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    TenantContext,
    get_seo_audit_service,
    get_seo_site_service,
    get_tenant_context,
    resolve_tenant_business_id,
)
from app.schemas.seo_audit import (
    SEOAuditFindingListResponse,
    SEOAuditFindingRead,
    SEOAuditRunCreateRequest,
    SEOAuditRunListResponse,
    SEOAuditRunRead,
)
from app.schemas.seo_site import (
    SEOSiteCreateRequest,
    SEOSiteListResponse,
    SEOSiteRead,
    SEOSiteUpdateRequest,
)
from app.services.seo_audit import SEOAuditNotFoundError, SEOAuditService, SEOAuditValidationError
from app.services.seo_sites import SEOSiteNotFoundError, SEOSiteService, SEOSiteValidationError

router = APIRouter(prefix="/api/businesses/{business_id}/seo", tags=["seo"])


@router.get("/sites", response_model=SEOSiteListResponse)
def list_seo_sites(
    business_id: str,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_site_service: SEOSiteService = Depends(get_seo_site_service),
) -> SEOSiteListResponse:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        items = seo_site_service.list_sites(business_id=scoped_business_id)
    except SEOSiteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SEOSiteListResponse(items=[SEOSiteRead.model_validate(site) for site in items], total=len(items))


@router.post("/sites", response_model=SEOSiteRead, status_code=status.HTTP_201_CREATED)
def create_seo_site(
    business_id: str,
    payload: SEOSiteCreateRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_site_service: SEOSiteService = Depends(get_seo_site_service),
) -> SEOSiteRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        site = seo_site_service.create_site(business_id=scoped_business_id, payload=payload)
    except SEOSiteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SEOSiteValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return SEOSiteRead.model_validate(site)


@router.get("/sites/{site_id}", response_model=SEOSiteRead)
def get_seo_site(
    business_id: str,
    site_id: str,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_site_service: SEOSiteService = Depends(get_seo_site_service),
) -> SEOSiteRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        site = seo_site_service.get_site(business_id=scoped_business_id, site_id=site_id)
    except SEOSiteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SEOSiteRead.model_validate(site)


@router.patch("/sites/{site_id}", response_model=SEOSiteRead)
def patch_seo_site(
    business_id: str,
    site_id: str,
    payload: SEOSiteUpdateRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_site_service: SEOSiteService = Depends(get_seo_site_service),
) -> SEOSiteRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        site = seo_site_service.update_site(
            business_id=scoped_business_id,
            site_id=site_id,
            payload=payload,
        )
    except SEOSiteNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SEOSiteValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return SEOSiteRead.model_validate(site)


@router.post("/sites/{site_id}/audit-runs", response_model=SEOAuditRunRead, status_code=status.HTTP_201_CREATED)
def create_seo_audit_run(
    business_id: str,
    site_id: str,
    payload: SEOAuditRunCreateRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_audit_service: SEOAuditService = Depends(get_seo_audit_service),
) -> SEOAuditRunRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        result = seo_audit_service.run_audit(
            business_id=scoped_business_id,
            site_id=site_id,
            payload=payload,
            created_by_principal_id=tenant_context.principal_id,
        )
    except SEOAuditNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SEOAuditValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return SEOAuditRunRead.model_validate(result.run)


@router.get("/sites/{site_id}/audit-runs", response_model=SEOAuditRunListResponse)
def list_seo_audit_runs(
    business_id: str,
    site_id: str,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_audit_service: SEOAuditService = Depends(get_seo_audit_service),
) -> SEOAuditRunListResponse:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        runs = seo_audit_service.list_runs_for_site(business_id=scoped_business_id, site_id=site_id)
    except SEOAuditNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SEOAuditRunListResponse(
        items=[SEOAuditRunRead.model_validate(run) for run in runs],
        total=len(runs),
    )


@router.get("/audit-runs/{run_id}", response_model=SEOAuditRunRead)
def get_seo_audit_run(
    business_id: str,
    run_id: str,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_audit_service: SEOAuditService = Depends(get_seo_audit_service),
) -> SEOAuditRunRead:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        run = seo_audit_service.get_run(business_id=scoped_business_id, run_id=run_id)
    except SEOAuditNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SEOAuditRunRead.model_validate(run)


@router.get("/audit-runs/{run_id}/findings", response_model=SEOAuditFindingListResponse)
def list_seo_audit_run_findings(
    business_id: str,
    run_id: str,
    tenant_context: TenantContext = Depends(get_tenant_context),
    seo_audit_service: SEOAuditService = Depends(get_seo_audit_service),
) -> SEOAuditFindingListResponse:
    scoped_business_id = resolve_tenant_business_id(
        tenant_context=tenant_context,
        requested_business_id=business_id,
    )
    try:
        findings = seo_audit_service.list_findings_for_run(business_id=scoped_business_id, run_id=run_id)
    except SEOAuditNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SEOAuditFindingListResponse(
        items=[SEOAuditFindingRead.model_validate(item) for item in findings],
        total=len(findings),
    )
