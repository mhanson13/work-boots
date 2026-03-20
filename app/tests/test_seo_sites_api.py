from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import TenantContext, get_db, get_tenant_context
from app.api.routes.seo import router as seo_router
from app.models.business import Business
from app.models.principal import Principal, PrincipalRole


def _override_tenant_context(
    business_id: str,
    principal_id: str | None = None,
    principal_role: PrincipalRole | None = None,
):
    def _resolver() -> TenantContext:
        return TenantContext(
            business_id=business_id,
            principal_id=principal_id or f"test-principal:{business_id}",
            auth_source="test",
            principal_role=principal_role,
        )

    return _resolver


def _make_client(
    db_session,
    *,
    business_id: str,
    principal_id: str | None = None,
    principal_role: PrincipalRole | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(seo_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_tenant_context] = _override_tenant_context(
        business_id,
        principal_id=principal_id,
        principal_role=principal_role,
    )
    return TestClient(app)


def test_seo_site_crud_and_business_scoping(db_session, seeded_business) -> None:
    other_business = Business(
        id=str(uuid4()),
        name="Other Tenant",
        notification_phone="+13035550199",
        notification_email="owner@other.example",
        sms_enabled=True,
        email_enabled=True,
        customer_auto_ack_enabled=True,
        contractor_alerts_enabled=True,
        timezone="America/Denver",
    )
    db_session.add(other_business)
    db_session.commit()

    client = _make_client(db_session, business_id=seeded_business.id)

    create_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={
            "display_name": "Main Site",
            "base_url": "https://Example.COM/",
            "industry": "Fire Restoration",
            "primary_location": "Denver, CO",
            "service_areas": ["Denver", "Lakewood"],
            "is_active": True,
            "is_primary": True,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["normalized_domain"] == "example.com"
    assert created["base_url"] == "https://example.com/"
    assert created["last_audit_run_id"] is None
    assert created["last_audit_status"] is None
    assert created["last_audit_completed_at"] is None

    site_id = created["id"]
    list_response = client.get(f"/api/businesses/{seeded_business.id}/seo/sites")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == site_id

    read_response = client.get(f"/api/businesses/{seeded_business.id}/seo/sites/{site_id}")
    assert read_response.status_code == 200

    patch_response = client.patch(
        f"/api/businesses/{seeded_business.id}/seo/sites/{site_id}",
        json={"display_name": "Main Site Updated", "base_url": "https://example.com/services/"},
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["display_name"] == "Main Site Updated"
    assert patched["base_url"] == "https://example.com/services"

    cross_tenant = client.get(f"/api/businesses/{other_business.id}/seo/sites/{site_id}")
    assert cross_tenant.status_code == 404


def test_seo_site_invalid_url_rejected(db_session, seeded_business) -> None:
    client = _make_client(db_session, business_id=seeded_business.id)
    response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={
            "display_name": "Bad URL Site",
            "base_url": "ftp://example.com",
        },
    )
    assert response.status_code == 422


def test_seo_site_duplicate_domain_rejected_for_business(db_session, seeded_business) -> None:
    client = _make_client(db_session, business_id=seeded_business.id)
    first = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={
            "display_name": "Main Site",
            "base_url": "https://example.com/",
        },
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={
            "display_name": "Duplicate Domain",
            "base_url": "https://EXAMPLE.com/services",
        },
    )
    assert duplicate.status_code == 422
    assert "already exists" in duplicate.json()["detail"].lower()


def test_admin_can_deactivate_and_reactivate_site(db_session, seeded_business) -> None:
    admin_principal = Principal(
        business_id=seeded_business.id,
        id="seo-admin",
        display_name="SEO Admin",
        role=PrincipalRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin_principal)
    db_session.commit()
    client = _make_client(db_session, business_id=seeded_business.id, principal_id=admin_principal.id)

    create_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={"display_name": "Main Site", "base_url": "https://example.com/"},
    )
    assert create_response.status_code == 201
    site_id = create_response.json()["id"]

    deactivate_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites/{site_id}/deactivate",
    )
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    activate_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites/{site_id}/activate",
    )
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True


def test_operator_cannot_deactivate_site(db_session, seeded_business) -> None:
    operator_principal = Principal(
        business_id=seeded_business.id,
        id="seo-operator",
        display_name="SEO Operator",
        role=PrincipalRole.OPERATOR,
        is_active=True,
    )
    db_session.add(operator_principal)
    db_session.commit()
    client = _make_client(db_session, business_id=seeded_business.id, principal_id=operator_principal.id)

    create_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={"display_name": "Main Site", "base_url": "https://example.com/"},
    )
    assert create_response.status_code == 201
    site_id = create_response.json()["id"]

    deactivate_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites/{site_id}/deactivate",
    )
    assert deactivate_response.status_code == 403


def test_operator_cannot_patch_site_activation_state(db_session, seeded_business) -> None:
    client = _make_client(
        db_session,
        business_id=seeded_business.id,
        principal_id="operator-test",
        principal_role=PrincipalRole.OPERATOR,
    )

    create_response = client.post(
        f"/api/businesses/{seeded_business.id}/seo/sites",
        json={"display_name": "Main Site", "base_url": "https://example.com/"},
    )
    assert create_response.status_code == 201
    site_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/api/businesses/{seeded_business.id}/seo/sites/{site_id}",
        json={"is_active": False},
    )
    assert patch_response.status_code == 403
