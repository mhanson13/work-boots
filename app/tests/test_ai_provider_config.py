from __future__ import annotations

import pytest

from app.api.deps import get_seo_competitor_profile_generation_provider
from app.core.config import get_settings
from app.integrations.seo_competitor_profile_generation_provider import (
    MisconfiguredSEOCompetitorProfileGenerationProvider,
    OpenAISEOCompetitorProfileGenerationProvider,
    SEOCompetitorProfileProviderError,
)
from app.integrations.seo_summary_provider import MockSEOCompetitorProfileGenerationProvider
from app.models.seo_site import SEOSite


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _site() -> SEOSite:
    return SEOSite(
        id="site-1",
        business_id="biz-1",
        display_name="Client Site",
        base_url="https://client.example/",
        normalized_domain="client.example",
        is_active=True,
        is_primary=True,
    )


def test_ai_provider_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_PROVIDER_API_KEY", raising=False)
    monkeypatch.delenv("AI_PROVIDER_NAME", raising=False)
    monkeypatch.delenv("AI_MODEL_NAME", raising=False)
    monkeypatch.delenv("AI_TIMEOUT_VALUE", raising=False)
    monkeypatch.delenv("AI_PROMPT_TEXT_RECOMMENDATION", raising=False)

    settings = get_settings()

    assert settings.ai_provider_api_key is None
    assert settings.ai_provider_name == "openai"
    assert settings.ai_model_name == "gpt-4o-mini"
    assert settings.ai_timeout_value == 30
    assert settings.ai_prompt_text_recommendation == ""


def test_ai_provider_config_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER_API_KEY", "sk-configured")
    monkeypatch.setenv("AI_PROVIDER_NAME", " OPENAI ")
    monkeypatch.setenv("AI_MODEL_NAME", " gpt-custom-model ")
    monkeypatch.setenv("AI_TIMEOUT_VALUE", "45")
    monkeypatch.setenv("AI_PROMPT_TEXT_RECOMMENDATION", "Prefer local competitors")

    settings = get_settings()

    assert settings.ai_provider_api_key == "sk-configured"
    assert settings.ai_provider_name == "openai"
    assert settings.ai_model_name == "gpt-custom-model"
    assert settings.ai_timeout_value == 45
    assert settings.ai_prompt_text_recommendation == "Prefer local competitors"


def test_provider_factory_uses_configured_model_timeout_and_prompt_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER_NAME", "openai")
    monkeypatch.setenv("AI_PROVIDER_API_KEY", "sk-test")
    monkeypatch.setenv("AI_MODEL_NAME", "gpt-configured")
    monkeypatch.setenv("AI_TIMEOUT_VALUE", "41")
    monkeypatch.setenv("AI_PROMPT_TEXT_RECOMMENDATION", "Prioritize direct local rivals")

    provider = get_seo_competitor_profile_generation_provider()

    assert isinstance(provider, OpenAISEOCompetitorProfileGenerationProvider)
    assert provider.model_name == "gpt-configured"
    assert provider.timeout_seconds == 41
    assert provider.prompt_text_recommendation == "Prioritize direct local rivals"


def test_provider_factory_missing_api_key_returns_safe_misconfigured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER_NAME", "openai")
    monkeypatch.setenv("AI_MODEL_NAME", "gpt-configured")
    monkeypatch.delenv("AI_PROVIDER_API_KEY", raising=False)

    provider = get_seo_competitor_profile_generation_provider()

    assert isinstance(provider, MisconfiguredSEOCompetitorProfileGenerationProvider)
    with pytest.raises(SEOCompetitorProfileProviderError) as exc_info:
        provider.generate_competitor_profiles(site=_site(), existing_domains=[], candidate_count=1)

    assert exc_info.value.code == "provider_auth_config"
    assert "credentials are not configured" in exc_info.value.safe_message.lower()


def test_provider_factory_invalid_provider_name_is_rejected_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER_NAME", "invalid-provider")
    monkeypatch.setenv("AI_MODEL_NAME", "invalid-model")
    monkeypatch.setenv("AI_PROVIDER_API_KEY", "sk-ignored")

    provider = get_seo_competitor_profile_generation_provider()

    assert isinstance(provider, MisconfiguredSEOCompetitorProfileGenerationProvider)
    with pytest.raises(SEOCompetitorProfileProviderError) as exc_info:
        provider.generate_competitor_profiles(site=_site(), existing_domains=[], candidate_count=1)

    assert exc_info.value.code == "provider_auth_config"
    assert "selection is invalid" in exc_info.value.safe_message.lower()


def test_provider_factory_supports_mock_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER_NAME", "mock")
    monkeypatch.setenv("AI_MODEL_NAME", "mock-model-configured")
    monkeypatch.delenv("AI_PROVIDER_API_KEY", raising=False)

    provider = get_seo_competitor_profile_generation_provider()

    assert isinstance(provider, MockSEOCompetitorProfileGenerationProvider)
    assert provider.model_name == "mock-model-configured"
