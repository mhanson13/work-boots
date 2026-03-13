from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.business_repository import BusinessRepository
from app.schemas.business import BusinessSettingsUpdateRequest


class BusinessSettingsService:
    def __init__(self, *, session: Session, business_repository: BusinessRepository) -> None:
        self.session = session
        self.business_repository = business_repository

    def get(self, *, business_id: str):
        business = self.business_repository.get(business_id)
        if not business:
            raise ValueError("Business not found")
        return business

    def update_settings(self, *, business_id: str, payload: BusinessSettingsUpdateRequest):
        business = self.business_repository.get(business_id)
        if not business:
            raise ValueError("Business not found")

        updates = payload.model_dump(exclude_unset=True)
        for field_name, value in updates.items():
            setattr(business, field_name, value)

        self.business_repository.save(business)
        self.session.commit()
        self.session.refresh(business)
        return business
