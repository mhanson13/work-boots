from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
import json
import urllib.error
import urllib.request

import pytest

from app.integrations.seo_recommendation_narrative_provider import (
    OpenAISEORecommendationNarrativeProvider,
    SEORecommendationNarrativeProviderError,
)
from app.models.seo_recommendation import SEORecommendation
from app.models.seo_recommendation_run import SEORecommendationRun


class _FakeHTTPResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _run() -> SEORecommendationRun:
    return SEORecommendationRun(
        id="run-1",
        business_id="biz-1",
        site_id="site-1",
        audit_run_id="audit-1",
        comparison_run_id=None,
        status="completed",
        total_recommendations=2,
        critical_recommendations=1,
        warning_recommendations=1,
        info_recommendations=0,
    )


def _recommendations() -> list[SEORecommendation]:
    return [
        SEORecommendation(
            id="rec-1",
            business_id="biz-1",
            site_id="site-1",
            recommendation_run_id="run-1",
            audit_run_id="audit-1",
            comparison_run_id=None,
            rule_key="fix_missing_title_tags",
            category="SEO",
            severity="WARNING",
            title="Fix missing title tags",
            rationale="Deterministic rationale one.",
            priority_score=70,
            priority_band="high",
            effort_bucket="LOW",
            status="open",
            created_at=datetime(2026, 3, 20, 12, 0, tzinfo=UTC),
        ),
        SEORecommendation(
            id="rec-2",
            business_id="biz-1",
            site_id="site-1",
            recommendation_run_id="run-1",
            audit_run_id="audit-1",
            comparison_run_id=None,
            rule_key="expand_thin_content_pages",
            category="CONTENT",
            severity="CRITICAL",
            title="Expand thin content pages",
            rationale="Deterministic rationale two.",
            priority_score=92,
            priority_band="critical",
            effort_bucket="HIGH",
            status="in_progress",
            created_at=datetime(2026, 3, 20, 13, 0, tzinfo=UTC),
        ),
    ]


def test_openai_recommendation_narrative_provider_parses_structured_response(monkeypatch) -> None:
    captured_payload: dict[str, object] = {}

    def _fake_urlopen(request: urllib.request.Request, timeout: int):  # noqa: ANN001
        assert timeout == 18
        request_body = request.data.decode("utf-8") if isinstance(request.data, bytes) else "{}"
        captured_payload.update(json.loads(request_body))
        response = {
            "model": "gpt-4.1-mini-2026-02-01",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "narrative_text": "Focus on title coverage and thin content first.",
                                "top_themes": ["metadata quality", "content depth"],
                                "sections": {
                                    "summary": "Deterministic recommendations were summarized.",
                                    "priority_rationale": "Critical content issues lead the backlog.",
                                    "next_actions": [
                                        "Address critical content pages first",
                                        "Then resolve warning metadata issues",
                                    ],
                                    "recommendation_references": ["rec-2", "unknown-id", "rec-2"],
                                },
                            }
                        )
                    }
                }
            ],
        }
        return _FakeHTTPResponse(json.dumps(response))

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    provider = OpenAISEORecommendationNarrativeProvider(
        api_key="sk-test",
        model_name="gpt-4.1-mini",
        timeout_seconds=18,
    )

    output = provider.generate_narrative(
        run=_run(),
        recommendations=_recommendations(),
        by_status={"open": 1, "in_progress": 1},
        by_category={"SEO": 1, "CONTENT": 1},
        by_severity={"WARNING": 1, "CRITICAL": 1},
        by_effort_bucket={"LOW": 1, "HIGH": 1},
        by_priority_band={"high": 1, "critical": 1},
        backlog=_recommendations(),
    )

    assert output.provider_name == "openai"
    assert output.model_name == "gpt-4.1-mini-2026-02-01"
    assert output.prompt_version == "seo-recommendation-narrative-v1"
    assert "Focus on title coverage" in output.narrative_text
    assert output.top_themes == ["metadata quality", "content depth"]
    assert isinstance(output.sections, dict)
    assert output.sections["recommendation_references"] == ["rec-2"]
    assert output.sections["status_rollup"] == {"in_progress": 1, "open": 1}
    assert captured_payload["model"] == "gpt-4.1-mini"
    assert captured_payload["response_format"]["type"] == "json_schema"


def test_openai_recommendation_narrative_provider_timeout_is_normalized(monkeypatch) -> None:
    def _timeout_urlopen(request: urllib.request.Request, timeout: int):  # noqa: ANN001
        del request, timeout
        raise TimeoutError("timeout")

    monkeypatch.setattr(urllib.request, "urlopen", _timeout_urlopen)
    provider = OpenAISEORecommendationNarrativeProvider(
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )

    with pytest.raises(SEORecommendationNarrativeProviderError) as exc_info:
        provider.generate_narrative(
            run=_run(),
            recommendations=_recommendations(),
            by_status={"open": 1},
            by_category={"SEO": 1},
            by_severity={"WARNING": 1},
            by_effort_bucket={"LOW": 1},
            by_priority_band={"high": 1},
            backlog=_recommendations(),
        )

    assert exc_info.value.code == "timeout"


def test_openai_recommendation_narrative_provider_auth_error_is_normalized(monkeypatch) -> None:
    def _unauthorized_urlopen(request: urllib.request.Request, timeout: int):  # noqa: ANN001
        del request, timeout
        raise urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":"invalid_api_key"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", _unauthorized_urlopen)
    provider = OpenAISEORecommendationNarrativeProvider(
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )

    with pytest.raises(SEORecommendationNarrativeProviderError) as exc_info:
        provider.generate_narrative(
            run=_run(),
            recommendations=_recommendations(),
            by_status={"open": 1},
            by_category={"SEO": 1},
            by_severity={"WARNING": 1},
            by_effort_bucket={"LOW": 1},
            by_priority_band={"high": 1},
            backlog=_recommendations(),
        )

    assert exc_info.value.code == "provider_auth_config"


def test_openai_recommendation_narrative_provider_malformed_content_is_normalized(monkeypatch) -> None:
    def _invalid_content_urlopen(request: urllib.request.Request, timeout: int):  # noqa: ANN001
        del request, timeout
        response = {
            "model": "gpt-4.1-mini",
            "choices": [{"message": {"content": "not-json"}}],
        }
        return _FakeHTTPResponse(json.dumps(response))

    monkeypatch.setattr(urllib.request, "urlopen", _invalid_content_urlopen)
    provider = OpenAISEORecommendationNarrativeProvider(
        api_key="sk-test",
        model_name="gpt-4.1-mini",
    )

    with pytest.raises(SEORecommendationNarrativeProviderError) as exc_info:
        provider.generate_narrative(
            run=_run(),
            recommendations=_recommendations(),
            by_status={"open": 1},
            by_category={"SEO": 1},
            by_severity={"WARNING": 1},
            by_effort_bucket={"LOW": 1},
            by_priority_band={"high": 1},
            backlog=_recommendations(),
        )

    assert exc_info.value.code == "invalid_output"
