from __future__ import annotations

from datetime import timedelta

from app.core.time import utc_now
from app.repositories.lead_repository import LeadRepository
from app.services.response_metrics import ResponseMetricsService


class LeadSummaryService:
    def __init__(
        self,
        lead_repository: LeadRepository,
        response_metrics_service: ResponseMetricsService,
    ) -> None:
        self.lead_repository = lead_repository
        self.response_metrics_service = response_metrics_service

    def get_summary(self, *, business_id: str, window: str = "7d") -> dict:
        now = utc_now()
        period = self._period_delta(window)
        start = now - period
        end = now

        by_status = self.lead_repository.status_counts(business_id, start=start, end=end)
        for key in ["new", "contacted", "estimate_scheduled", "won", "lost"]:
            by_status.setdefault(key, 0)

        total = sum(by_status.values())
        metrics = self.response_metrics_service.compute_snapshot(
            business_id=business_id,
            start=start,
            end=end,
        )

        return {
            "by_status": by_status,
            "total_leads": total,
            "new_leads": by_status.get("new", 0),
            "leads_awaiting_response": metrics.leads_awaiting_first_response,
            "stale_15m_count": metrics.stale_15m_count,
            "stale_2h_count": metrics.stale_2h_count,
            "avg_response_minutes": metrics.avg_response_minutes,
            "median_response_minutes": metrics.median_response_minutes,
            # Backward-compat fields from Phase 1/2 contract.
            "avg_minutes_to_first_response": metrics.avg_response_minutes,
            "uncontacted_over_30_min": metrics.stale_30m_count,
            "period_start": start,
            "period_end": end,
        }

    def _period_delta(self, window: str) -> timedelta:
        if window == "24h":
            return timedelta(hours=24)
        if window == "30d":
            return timedelta(days=30)
        return timedelta(days=7)
