from __future__ import annotations

from app.services.reminder_engine import ReminderEngineService, ReminderRunResult


class LeadReminderJob:
    """Manual/scheduled entry point for the Phase 3 reminder engine."""

    def __init__(self, reminder_engine: ReminderEngineService) -> None:
        self.reminder_engine = reminder_engine

    def run(self, *, business_id: str) -> ReminderRunResult:
        return self.reminder_engine.run_for_business(business_id=business_id)
