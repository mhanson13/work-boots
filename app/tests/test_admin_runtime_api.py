from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.routes.admin_runtime as admin_runtime_routes
from app.api.deps import TenantContext, get_db, get_tenant_context
from app.api.routes.admin_runtime import router as admin_runtime_router
from app.models.principal import Principal, PrincipalRole
from app.schemas.admin_logs import ADCRuntimeCheckResponse


def _make_client(
    db_session,
    *,
    business_id: str,
    principal_id: str = "admin-1",
    principal_role: PrincipalRole = PrincipalRole.ADMIN,
) -> TestClient:
    principal = db_session.get(Principal, (business_id, principal_id))
    if principal is None:
        db_session.add(
            Principal(
                business_id=business_id,
                id=principal_id,
                display_name=principal_id,
                role=principal_role,
                is_active=True,
            )
        )
    else:
        principal.role = principal_role
        principal.is_active = True
    db_session.commit()

    app = FastAPI()
    app.include_router(admin_runtime_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_tenant_context() -> TenantContext:
        return TenantContext(
            business_id=business_id,
            principal_id=principal_id,
            auth_source="test",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_tenant_context] = override_tenant_context
    return TestClient(app)


def test_admin_runtime_adc_check_requires_admin_principal(db_session, seeded_business) -> None:
    client = _make_client(
        db_session,
        business_id=seeded_business.id,
        principal_id="operator-1",
        principal_role=PrincipalRole.OPERATOR,
    )

    response = client.get("/admin/runtime/adc-check")

    assert response.status_code == 403
    assert "not allowed" in response.json()["detail"]


def test_admin_runtime_adc_check_endpoint_returns_status_payload(db_session, seeded_business, monkeypatch) -> None:
    expected = ADCRuntimeCheckResponse(
        adc_available=True,
        project_id="mbsrn-prod",
        error=None,
        phase=None,
        cause_class=None,
        credentials_class="Credentials",
    )
    monkeypatch.setattr(
        admin_runtime_routes,
        "_resolve_adc_runtime_status",
        lambda: expected,
    )
    client = _make_client(
        db_session,
        business_id=seeded_business.id,
    )

    response = client.get("/admin/runtime/adc-check")

    assert response.status_code == 200
    assert response.json() == {
        "adc_available": True,
        "project_id": "mbsrn-prod",
        "error": None,
        "phase": None,
        "cause_class": None,
        "credentials_class": "Credentials",
    }


def test_resolve_adc_runtime_status_returns_false_when_adc_unavailable(monkeypatch) -> None:
    def _failing_auth_loader():
        raise ImportError("google.auth transport missing")

    monkeypatch.setattr(admin_runtime_routes, "_load_google_auth", _failing_auth_loader)

    response = admin_runtime_routes._resolve_adc_runtime_status()

    assert response.adc_available is False
    assert response.project_id is None
    assert response.phase == "dependency_missing"
    assert response.cause_class == "ImportError"
    assert response.credentials_class is None
    assert response.error is not None
    assert "google.auth transport missing" in response.error


def test_resolve_adc_runtime_status_returns_true_when_token_refresh_succeeds(monkeypatch) -> None:
    class _FakeCredentials:
        def __init__(self) -> None:
            self.token = ""
            self.valid = False

        def refresh(self, _request) -> None:
            self.valid = True
            self.token = "test-token"

    class _FakeAuthRequest:
        pass

    def _fake_google_auth_default(*, scopes):
        assert scopes == [admin_runtime_routes._CLOUD_LOGGING_READ_SCOPE]
        return _FakeCredentials(), "mbsrn-prod"

    monkeypatch.setattr(
        admin_runtime_routes,
        "_load_google_auth",
        lambda: (_fake_google_auth_default, _FakeAuthRequest),
    )

    response = admin_runtime_routes._resolve_adc_runtime_status()

    assert response.adc_available is True
    assert response.project_id == "mbsrn-prod"
    assert response.error is None
    assert response.phase is None
    assert response.cause_class is None
    assert response.credentials_class == "_FakeCredentials"


def test_resolve_adc_runtime_status_returns_refresh_phase_on_refresh_failure(monkeypatch) -> None:
    class _FakeCredentials:
        def __init__(self) -> None:
            self.token = ""
            self.valid = False

        def refresh(self, _request) -> None:
            raise RuntimeError("metadata token exchange failed")

    class _FakeAuthRequest:
        pass

    def _fake_google_auth_default(*, scopes):
        assert scopes == [admin_runtime_routes._CLOUD_LOGGING_READ_SCOPE]
        return _FakeCredentials(), "mbsrn-prod"

    monkeypatch.setattr(
        admin_runtime_routes,
        "_load_google_auth",
        lambda: (_fake_google_auth_default, _FakeAuthRequest),
    )

    response = admin_runtime_routes._resolve_adc_runtime_status()

    assert response.adc_available is False
    assert response.project_id == "mbsrn-prod"
    assert response.phase == "token_refresh_failure"
    assert response.cause_class == "RuntimeError"
    assert response.credentials_class == "_FakeCredentials"
    assert response.error is not None
    assert "metadata token exchange failed" in response.error
