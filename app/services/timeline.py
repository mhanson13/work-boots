from __future__ import annotations

from app.models.lead_event import LeadEvent
from app.repositories.lead_repository import LeadRepository


class LeadTimelineService:
    def __init__(self, lead_repository: LeadRepository) -> None:
        self.lead_repository = lead_repository

    def get_timeline(self, *, lead_id: str) -> list[LeadEvent]:
        lead = self.lead_repository.get(lead_id)
        if not lead:
            raise ValueError("Lead not found")
        return self.lead_repository.list_events_for_lead(lead_id)
