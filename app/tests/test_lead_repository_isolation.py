from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from app.core.time import utc_now
from app.models.business import Business
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.lead_event import ActorType, LeadEvent, LeadEventType
from app.repositories.lead_repository import LeadRepository


def _seed_other_business(db_session) -> Business:
    business = Business(
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
    db_session.add(business)
    db_session.flush()
    return business


def _seed_lead(db_session, business_id: str, *, customer_name: str) -> Lead:
    lead = Lead(
        id=str(uuid4()),
        business_id=business_id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=utc_now() - timedelta(minutes=10),
        customer_name=customer_name,
        phone="3035550101",
        status=LeadStatus.NEW,
    )
    db_session.add(lead)
    db_session.flush()
    return lead


def test_get_for_business_is_scoped(db_session, seeded_business) -> None:
    repository = LeadRepository(db_session)
    other_business = _seed_other_business(db_session)
    other_lead = _seed_lead(db_session, other_business.id, customer_name="Other Lead")
    db_session.commit()

    assert repository.get_for_business(seeded_business.id, other_lead.id) is None
    assert repository.get_for_business(other_business.id, other_lead.id) is not None


def test_list_events_for_business_methods_prevent_cross_tenant_leakage(db_session, seeded_business) -> None:
    repository = LeadRepository(db_session)
    other_business = _seed_other_business(db_session)
    lead_a = _seed_lead(db_session, seeded_business.id, customer_name="Tenant A Lead")
    lead_b = _seed_lead(db_session, other_business.id, customer_name="Tenant B Lead")

    db_session.add_all(
        [
            LeadEvent(
                id=str(uuid4()),
                business_id=seeded_business.id,
                lead_id=lead_a.id,
                event_type=LeadEventType.LEAD_CREATED.value,
                actor_type=ActorType.SYSTEM,
                payload_json={},
            ),
            LeadEvent(
                id=str(uuid4()),
                business_id=other_business.id,
                lead_id=lead_b.id,
                event_type=LeadEventType.LEAD_CREATED.value,
                actor_type=ActorType.SYSTEM,
                payload_json={},
            ),
        ]
    )
    db_session.commit()

    tenant_a_events = repository.list_events_for_business(seeded_business.id)
    assert len(tenant_a_events) == 1
    assert tenant_a_events[0].business_id == seeded_business.id
    assert tenant_a_events[0].lead_id == lead_a.id

    assert repository.list_events_for_business_lead(seeded_business.id, lead_b.id) == []
    assert len(repository.list_events_for_business_lead(seeded_business.id, lead_a.id)) == 1


def test_add_event_backfills_business_id_from_lead(db_session, seeded_business) -> None:
    repository = LeadRepository(db_session)
    lead = _seed_lead(db_session, seeded_business.id, customer_name="Backfill Lead")
    event = LeadEvent(
        id=str(uuid4()),
        business_id=None,  # type: ignore[arg-type]
        lead_id=lead.id,
        event_type=LeadEventType.NOTE.value,
        actor_type=ActorType.OWNER,
        payload_json={"note": "hello"},
    )

    repository.add_event(event)
    db_session.commit()
    assert event.business_id == seeded_business.id


def test_add_event_rejects_mismatched_business_id(db_session, seeded_business) -> None:
    repository = LeadRepository(db_session)
    other_business = _seed_other_business(db_session)
    lead = _seed_lead(db_session, seeded_business.id, customer_name="Mismatch Lead")
    event = LeadEvent(
        id=str(uuid4()),
        business_id=other_business.id,
        lead_id=lead.id,
        event_type=LeadEventType.NOTE.value,
        actor_type=ActorType.OWNER,
        payload_json={"note": "bad scope"},
    )

    with pytest.raises(ValueError, match="Event business_id does not match lead ownership"):
        repository.add_event(event)
