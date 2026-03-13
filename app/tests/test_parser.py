from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.lead import LeadSource, LeadStatus
from app.repositories.business_repository import BusinessRepository
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import ManualIntakeRequest
from app.services.lead_intake import LeadIntakeService


def test_manual_lead_creation_service(db_session: Session, seeded_business) -> None:
    service = LeadIntakeService(
        session=db_session,
        business_repository=BusinessRepository(db_session),
        lead_repository=LeadRepository(db_session),
    )

    lead = service.create_manual_lead(
        ManualIntakeRequest(
            business_id=seeded_business.id,
            submitted_at=utc_now() - timedelta(minutes=5),
            customer_name="Jamie",
            phone="+13035550123",
            email="jamie@example.com",
            service_type="fire restoration",
            city="Denver",
            message="Need estimate",
            estimated_job_value=3500,
        )
    )

    assert lead.id is not None
    assert lead.business_id == seeded_business.id
    assert lead.source == LeadSource.MANUAL
    assert lead.status == LeadStatus.NEW
