from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.lead import LeadStatus
from app.models.lead_event import ActorType
from app.repositories.lead_repository import LeadRepository
from app.services.lifecycle import InvalidStatusTransitionError, LeadLifecycleService


def test_status_transition_validation(db_session: Session, sample_lead) -> None:
    lifecycle = LeadLifecycleService(session=db_session, lead_repository=LeadRepository(db_session))

    updated, previous = lifecycle.patch_status(
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
        lead_id=sample_lead.id,
        next_status=LeadStatus.CONTACTED,
        actor_type=ActorType.OWNER,
        actor_id="owner-1",
        event_note=None,
    )

    with pytest.raises(InvalidStatusTransitionError):
        lifecycle.patch_status(
            lead_id=sample_lead.id,
            next_status=LeadStatus.NEW,
            actor_type=ActorType.OWNER,
            actor_id="owner-1",
            event_note=None,
        )
