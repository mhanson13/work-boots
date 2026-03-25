from __future__ import annotations

from app.repositories.business_repository import BusinessRepository
from app.repositories.seo_competitor_profile_generation_repository import (
    SEOCompetitorProfileGenerationRepository,
)
from app.repositories.seo_competitor_repository import SEOCompetitorRepository
from app.repositories.seo_recommendation_narrative_repository import (
    SEORecommendationNarrativeRepository,
)
from app.repositories.seo_recommendation_repository import SEORecommendationRepository
from app.repositories.seo_site_repository import SEOSiteRepository
from app.services.seo_competitor_profile_generation import SEOCompetitorProfileGenerationService
from app.services.seo_recommendation_narratives import SEORecommendationNarrativeService


class _MutablePromptProvider:
    provider_name = "test-provider"
    model_name = "test-model"
    prompt_version = "test-prompt-v1"

    def __init__(
        self,
        *,
        competitor_prompt_text: str = "",
        recommendation_prompt_text: str = "",
        legacy_config_used: bool = False,
    ) -> None:
        self.prompt_text_competitor = competitor_prompt_text
        self.prompt_text_recommendations = recommendation_prompt_text
        # Legacy compatibility fields intentionally mirror modern fields.
        self.prompt_text_recommendation = recommendation_prompt_text or competitor_prompt_text
        self.legacy_config_used = legacy_config_used
        self.prompt_source = "env"


def test_competitor_prompt_fallback_resolution_uses_immutable_snapshot_not_mutable_provider(
    db_session,
    seeded_business,
) -> None:
    provider = _MutablePromptProvider(competitor_prompt_text="Configured competitor fallback prompt.")
    service = SEOCompetitorProfileGenerationService(
        session=db_session,
        business_repository=BusinessRepository(db_session),
        seo_site_repository=SEOSiteRepository(db_session),
        seo_competitor_repository=SEOCompetitorRepository(db_session),
        seo_competitor_profile_generation_repository=SEOCompetitorProfileGenerationRepository(db_session),
        provider=provider,
    )

    # Simulate runtime mutation performed during run execution.
    provider.prompt_text_competitor = "MUTATED RUNTIME VALUE"
    provider.prompt_text_recommendation = "MUTATED LEGACY VALUE"
    seeded_business.ai_prompt_text_competitor = None

    resolved = service._resolve_competitor_prompt_settings(seeded_business)
    assert resolved.prompt_text == "Configured competitor fallback prompt."
    assert resolved.prompt_source == "env"


def test_recommendation_prompt_fallback_resolution_uses_immutable_snapshot_not_mutable_provider(
    db_session,
    seeded_business,
) -> None:
    provider = _MutablePromptProvider(recommendation_prompt_text="Configured recommendation fallback prompt.")
    service = SEORecommendationNarrativeService(
        session=db_session,
        business_repository=BusinessRepository(db_session),
        seo_recommendation_repository=SEORecommendationRepository(db_session),
        seo_recommendation_narrative_repository=SEORecommendationNarrativeRepository(db_session),
        seo_competitor_profile_generation_repository=SEOCompetitorProfileGenerationRepository(db_session),
        provider=provider,
    )

    # Simulate runtime mutation performed during narrative generation.
    provider.prompt_text_recommendations = "MUTATED RUNTIME VALUE"
    provider.prompt_text_recommendation = "MUTATED LEGACY VALUE"
    seeded_business.ai_prompt_text_recommendations = None

    resolved = service._resolve_recommendation_prompt_settings(seeded_business)
    assert resolved.prompt_text == "Configured recommendation fallback prompt."
    assert resolved.prompt_source == "env"

