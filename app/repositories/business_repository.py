from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business import Business


class BusinessRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, business_id: str) -> Business | None:
        return self.session.get(Business, business_id)

    def get_or_create(
        self,
        business_id: str,
        name: str = "Default Contractor",
        notification_email: str | None = None,
        notification_phone: str | None = None,
    ) -> Business:
        business = self.get(business_id)
        if business:
            return business

        business = Business(
            id=business_id,
            name=name,
            primary_phone=notification_phone,
            notification_phone=notification_phone,
            notification_email=notification_email,
            customer_auto_ack_enabled=True,
            contractor_alerts_enabled=True,
        )
        self.session.add(business)
        self.session.flush()
        return business

    def list(self) -> list[Business]:
        stmt = select(Business).order_by(Business.name.asc())
        return list(self.session.scalars(stmt))

    def save(self, business: Business) -> Business:
        self.session.add(business)
        self.session.flush()
        return business
