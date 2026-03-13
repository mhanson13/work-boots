from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from app.core.time import utc_now
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.lead_event import ActorType, LeadEvent, LeadEventType
from app.repositories.lead_repository import LeadRepository
from app.services.response_metrics import ResponseMetricsService
from app.services.summary import LeadSummaryService


def test_response_metrics_with_status_fallback(db_session, seeded_business) -> None:
    now = utc_now()

    responded_direct = Lead(
        id=str(uuid4()),
        business_id=seeded_business.id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(hours=6),
        customer_name="Direct Response",
        phone="3035550101",
        status=LeadStatus.CONTACTED,
        first_human_response_at=now - timedelta(hours=5, minutes=40),
    )
    responded_fallback = Lead(
        id=str(uuid4()),
        business_id=seeded_business.id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(hours=4),
        customer_name="Fallback Response",
        phone="3035550102",
        status=LeadStatus.CONTACTED,
        first_human_response_at=None,
    )
    stale_20m = Lead(
        id=str(uuid4()),
        business_id=seeded_business.id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(minutes=20),
        customer_name="Stale 20m",
        phone="3035550103",
        status=LeadStatus.NEW,
    )
    stale_3h = Lead(
        id=str(uuid4()),
        business_id=seeded_business.id,
        source=LeadSource.MANUAL,
        source_ref=None,
        submitted_at=now - timedelta(hours=3),
        customer_name="Stale 3h",
        phone="3035550104",
        status=LeadStatus.NEW,
    )
    db_session.add_all([responded_direct, responded_fallback, stale_20m, stale_3h])
    db_session.flush()

    db_session.add(
        LeadEvent(
            id=str(uuid4()),
            lead_id=responded_fallback.id,
            event_type=LeadEventType.STATUS_CHANGED.value,
            event_timestamp=now - timedelta(hours=3, minutes=15),  # 45 minutes after submit
            actor_type=ActorType.OWNER,
            payload_json={"from": "new", "to": "contacted"},
        )
    )
    db_session.commit()

    repository = LeadRepository(db_session)
    metrics_service = ResponseMetricsService(lead_repository=repository)
    snapshot = metrics_service.compute_snapshot(
        business_id=seeded_business.id,
        start=now - timedelta(days=7),
        end=now,
    )

    assert snapshot.avg_response_minutes == 32.5
    assert snapshot.median_response_minutes == 32.5
    assert snapshot.responded_leads_count == 2
    assert snapshot.leads_awaiting_first_response == 2
    assert snapshot.stale_15m_count == 2
    assert snapshot.stale_2h_count == 1


def test_summary_service_includes_phase3_operational_fields(db_session, seeded_business) -> None:
    now = utc_now()
    db_session.add(
        Lead(
            id=str(uuid4()),
            business_id=seeded_business.id,
            source=LeadSource.MANUAL,
            source_ref=None,
            submitted_at=now - timedelta(minutes=40),
            customer_name="Awaiting",
            phone="3035550199",
            status=LeadStatus.NEW,
        )
    )
    db_session.commit()

    repository = LeadRepository(db_session)
    summary_service = LeadSummaryService(
        lead_repository=repository,
        response_metrics_service=ResponseMetricsService(lead_repository=repository),
    )
    summary = summary_service.get_summary(business_id=seeded_business.id, window="7d")

    assert "new_leads" in summary
    assert "leads_awaiting_response" in summary
    assert "stale_15m_count" in summary
    assert "stale_2h_count" in summary
    assert "avg_response_minutes" in summary
    assert "median_response_minutes" in summary
