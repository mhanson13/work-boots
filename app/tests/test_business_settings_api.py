from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.api.routes.businesses import router as businesses_router


def test_get_business_settings_endpoint(db_session, seeded_business) -> None:
    app = FastAPI()
    app.include_router(businesses_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get(f"/api/businesses/{seeded_business.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == seeded_business.id
    assert payload["sms_enabled"] is True
    assert payload["email_enabled"] is True
    assert payload["customer_auto_ack_enabled"] is True
    assert payload["contractor_alerts_enabled"] is True


def test_patch_business_settings_endpoint(db_session, seeded_business) -> None:
    app = FastAPI()
    app.include_router(businesses_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.patch(
        f"/api/businesses/{seeded_business.id}/settings",
        json={
            "sms_enabled": False,
            "email_enabled": True,
            "customer_auto_ack_enabled": False,
            "contractor_alerts_enabled": True,
            "timezone": "America/Chicago",
            "notification_phone": "+13035551234",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sms_enabled"] is False
    assert payload["customer_auto_ack_enabled"] is False
    assert payload["timezone"] == "America/Chicago"
    assert payload["notification_phone"] == "+13035551234"
