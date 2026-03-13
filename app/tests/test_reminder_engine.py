from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.deps import get_db
from app.api.routes.jobs import router as jobs_router
from app.core.time import utc_now
from app.integrations import MockEmailProvider, MockSMSProvider
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.lead_event import LeadEvent
from app.repositories.business_repository import BusinessRepository
from app.repositories.lead_repository import LeadRepository
from app.services.notifications import NotificationService
from app.services.reminder_engine import ReminderEngineService


def _seed_reminder_leads(db_session, business_id: str) -> tuple[str, str, str]:
    now = utc_now()
    lead_16m = Lead(
        id=str(uuid4()),
        business_id=business_id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(minutes=16),
        customer_name="Lead 16m",
        phone="3035550201",
        status=LeadStatus.NEW,
    )
    lead_130m = Lead(
        id=str(uuid4()),
        business_id=business_id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(minutes=130),
        customer_name="Lead 130m",
        phone="3035550202",
        status=LeadStatus.NEW,
    )
    lead_5m = Lead(
        id=str(uuid4()),
        business_id=business_id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(minutes=5),
        customer_name="Lead 5m",
        phone="3035550203",
        status=LeadStatus.NEW,
    )
    db_session.add_all([lead_16m, lead_130m, lead_5m])
    db_session.commit()
    return lead_16m.id, lead_130m.id, lead_5m.id


def test_reminder_engine_eligibility_and_duplicate_suppression(db_session, seeded_business) -> None:
    lead_16m_id, lead_130m_id, _ = _seed_reminder_leads(db_session, seeded_business.id)

    notification_service = NotificationService(
        lead_repository=LeadRepository(db_session),
        email_provider=MockEmailProvider(),
        sms_provider=MockSMSProvider(),
    )
    engine = ReminderEngineService(
        session=db_session,
        business_repository=BusinessRepository(db_session),
        lead_repository=LeadRepository(db_session),
        notification_service=notification_service,
    )

    first_run = engine.run_for_business(business_id=seeded_business.id)
    assert first_run.scanned_leads == 3
    assert first_run.reminder_15m_sent == 2
    assert first_run.reminder_2h_sent == 1
    assert first_run.reminders_sent == 3

    event_rows = list(
        db_session.execute(select(LeadEvent.lead_id, LeadEvent.event_type)).all()
    )
    lead_16m_events = [event_type for lead_id, event_type in event_rows if lead_id == lead_16m_id]
    lead_130m_events = [event_type for lead_id, event_type in event_rows if lead_id == lead_130m_id]

    assert "reminder_15m_triggered" in lead_16m_events
    assert "reminder_15m_triggered" in lead_130m_events
    assert "reminder_2h_triggered" in lead_130m_events
    assert "notification_dispatch_sent" in lead_16m_events
    assert "notification_dispatch_sent" in lead_130m_events

    second_run = engine.run_for_business(business_id=seeded_business.id)
    assert second_run.reminders_sent == 0
    assert second_run.reminder_15m_sent == 0
    assert second_run.reminder_2h_sent == 0


def test_manual_reminder_run_endpoint(db_session, seeded_business) -> None:
    _seed_reminder_leads(db_session, seeded_business.id)

    app = FastAPI()
    app.include_router(jobs_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post(
        "/api/jobs/lead-reminders/run",
        json={"business_id": seeded_business.id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["business_id"] == seeded_business.id
    assert payload["scanned_leads"] == 3
    assert payload["reminders_sent"] >= 1
