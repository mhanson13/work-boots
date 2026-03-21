from __future__ import annotations

from app.services.seo_competitor_profile_generation import (
    SEOCompetitorProfileGenerationService,
    SEOCompetitorProfileRetentionCleanupSummary,
)


class SEOCompetitorProfileGenerationRetentionJob:
    """Scheduler-ready entrypoint for competitor profile retention cleanup."""

    def __init__(self, generation_service: SEOCompetitorProfileGenerationService) -> None:
        self.generation_service = generation_service

    def run_cleanup(
        self,
        *,
        business_id: str,
        site_id: str | None = None,
    ) -> SEOCompetitorProfileRetentionCleanupSummary:
        return self.generation_service.cleanup_retention(business_id=business_id, site_id=site_id)
