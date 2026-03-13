from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median

from app.models.lead import LeadStatus
from app.models.lead_event import LeadEventType
from app.repositories.lead_repository import LeadRepository


@dataclass(frozen=True)
class ResponseMetricsSnapshot:
    avg_response_minutes: float | None
    median_response_minutes: float | None
    responded_leads_count: int
    leads_awaiting_first_response: int
    stale_15m_count: int
    stale_2h_count: int
    stale_30m_count: int


class ResponseMetricsService:
    def __init__(self, lead_repository: LeadRepository) -> None:
        self.lead_repository = lead_repository

    def compute_snapshot(
        self,
        *,
        business_id: str,
        start: datetime,
        end: datetime,
    ) -> ResponseMetricsSnapshot:
        leads = self.lead_repository.list_submitted_between(
            business_id=business_id,
            start=start,
            end=end,
        )

        missing_response_ids = [lead.id for lead in leads if lead.first_human_response_at is None]
        fallback_response_map = self._fallback_response_map(missing_response_ids)

        deltas_minutes: list[float] = []
        for lead in leads:
            response_at = lead.first_human_response_at or fallback_response_map.get(lead.id)
            if response_at is None:
                continue

            delta = (response_at - lead.submitted_at).total_seconds() / 60.0
            deltas_minutes.append(max(delta, 0.0))

        avg_response = round(sum(deltas_minutes) / len(deltas_minutes), 1) if deltas_minutes else None
        median_response = round(float(median(deltas_minutes)), 1) if deltas_minutes else None

        return ResponseMetricsSnapshot(
            avg_response_minutes=avg_response,
            median_response_minutes=median_response,
            responded_leads_count=len(deltas_minutes),
            leads_awaiting_first_response=self.lead_repository.count_awaiting_first_response(business_id),
            stale_15m_count=self.lead_repository.count_stale_new_leads(business_id, minutes=15),
            stale_2h_count=self.lead_repository.count_stale_new_leads(business_id, minutes=120),
            stale_30m_count=self.lead_repository.count_stale_new_leads(business_id, minutes=30),
        )

    def _fallback_response_map(self, lead_ids: list[str]) -> dict[str, datetime]:
        events = self.lead_repository.list_events_for_leads(
            lead_ids,
            event_types=[LeadEventType.STATUS_CHANGED.value],
        )
        fallback: dict[str, datetime] = {}
        for event in events:
            payload = event.payload_json or {}
            next_status = str(payload.get("to", "")).lower().strip()
            if not next_status or next_status == LeadStatus.NEW.value:
                continue
            if event.lead_id not in fallback:
                fallback[event.lead_id] = event.event_timestamp
        return fallback
