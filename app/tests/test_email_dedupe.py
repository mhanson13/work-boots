from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.core.time import utc_now
from app.models.lead import Lead, LeadSource, LeadStatus
from app.repositories.lead_repository import LeadRepository
from app.services.dedupe import LeadDeduplicationService


def test_dedupe_hit_same_phone_within_7_days(db_session, seeded_business) -> None:
    existing = Lead(
        id=str(uuid4()),
        business_id=seeded_business.id,
        source=LeadSource.GODADDY_EMAIL,
        source_ref="old-1",
        submitted_at=utc_now() - timedelta(days=2),
        customer_name="Ava Turner",
        phone="+13035550188",
        email="ava@example.com",
        service_type="Fire cleanup",
        city="Denver",
        message="Original request",
        status=LeadStatus.NEW,
    )
    db_session.add(existing)
    db_session.commit()

    service = LeadDeduplicationService(lead_repository=LeadRepository(db_session))
    match = service.find_duplicate(
        business_id=seeded_business.id,
        submitted_at=utc_now(),
        customer_name="Ava Turner",
        phone="303-555-0188",
        email=None,
    )

    assert match is not None
    assert match.lead.id == existing.id
    assert match.rule in {"same_name_phone_same_day", "same_phone_7d"}


def test_dedupe_miss_outside_7_day_window(db_session, seeded_business) -> None:
    old = Lead(
        id=str(uuid4()),
        business_id=seeded_business.id,
        source=LeadSource.GODADDY_EMAIL,
        source_ref="old-2",
        submitted_at=utc_now() - timedelta(days=10),
        customer_name="Chris Brown",
        phone="+13035550199",
        email="chris@example.com",
        service_type="Board-up",
        city="Aurora",
        message="Old lead",
        status=LeadStatus.NEW,
    )
    db_session.add(old)
    db_session.commit()

    service = LeadDeduplicationService(lead_repository=LeadRepository(db_session))
    match = service.find_duplicate(
        business_id=seeded_business.id,
        submitted_at=utc_now(),
        customer_name="Chris Brown",
        phone="+13035550199",
        email="chris@example.com",
    )

    assert match is None
