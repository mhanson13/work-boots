from __future__ import annotations

import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.business import Business
from app.models.lead import LeadStatus
from app.models.lead_event import ActorType
from app.repositories.lead_repository import LeadRepository
from app.services.lifecycle import InvalidStatusTransitionError, LeadLifecycleService


def test_status_transition_validation(db_session: Session, sample_lead) -> None:
    lifecycle = LeadLifecycleService(session=db_session, lead_repository=LeadRepository(db_session))

    updated, previous = lifecycle.patch_status(
        business_id=sample_lead.business_id,
        lead_id=sample_lead.id,
        next_status=LeadStatus.CONTACTED,
        actor_type=ActorType.OWNER,
        actor_id="owner-1",
        event_note=None,
    )

    assert previous == LeadStatus.NEW
    assert updated.status == LeadStatus.CONTACTED


def test_invalid_status_transition_raises(db_session: Session, sample_lead) -> None:
    lifecycle = LeadLifecycleService(session=db_session, lead_repository=LeadRepository(db_session))

    lifecycle.patch_status(
        business_id=sample_lead.business_id,
        lead_id=sample_lead.id,
        next_status=LeadStatus.CONTACTED,
        actor_type=ActorType.OWNER,
        actor_id="owner-1",
        event_note=None,
    )

    with pytest.raises(InvalidStatusTransitionError):
        lifecycle.patch_status(
            business_id=sample_lead.business_id,
            lead_id=sample_lead.id,
            next_status=LeadStatus.NEW,
            actor_type=ActorType.OWNER,
            actor_id="owner-1",
            event_note=None,
        )


def test_cross_business_status_update_rejected(db_session: Session, sample_lead) -> None:
    lifecycle = LeadLifecycleService(session=db_session, lead_repository=LeadRepository(db_session))
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

    with pytest.raises(ValueError, match="Lead not found"):
        lifecycle.patch_status(
            business_id=other_business.id,
            lead_id=sample_lead.id,
            next_status=LeadStatus.CONTACTED,
            actor_type=ActorType.OWNER,
            actor_id="owner-1",
            event_note=None,
        )
