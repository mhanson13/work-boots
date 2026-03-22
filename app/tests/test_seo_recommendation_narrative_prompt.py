from __future__ import annotations

from datetime import UTC, datetime

from app.models.seo_recommendation import SEORecommendation
from app.models.seo_recommendation_run import SEORecommendationRun
from app.services.seo_recommendation_narrative_prompt import (
    SEO_RECOMMENDATION_NARRATIVE_PROMPT_VERSION,
    build_seo_recommendation_narrative_prompt,
)


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
            rationale="Pages are thin and need meaningful depth updates.",
            priority_score=90,
            priority_band="critical",
            effort_bucket="HIGH",
            status="open",
            created_at=datetime(2026, 3, 20, 12, 0, tzinfo=UTC),
        ),
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
            rationale="A" * 500,
            priority_score=70,
            priority_band="high",
            effort_bucket="LOW",
            status="in_progress",
            created_at=datetime(2026, 3, 20, 11, 0, tzinfo=UTC),
        ),
    ]


def test_prompt_contains_grounded_deterministic_context() -> None:
    prompt = build_seo_recommendation_narrative_prompt(
        run=_run(),
        recommendations=_recommendations(),
        by_status={"open": 1, "in_progress": 1},
        by_category={"SEO": 1, "CONTENT": 1},
        by_severity={"CRITICAL": 1, "WARNING": 1},
        by_effort_bucket={"HIGH": 1, "LOW": 1},
        by_priority_band={"critical": 1, "high": 1},
        backlog=_recommendations(),
    )

    assert prompt.prompt_version == SEO_RECOMMENDATION_NARRATIVE_PROMPT_VERSION
    assert "RECOMMENDATION_CONTEXT_JSON" in prompt.user_prompt
    assert prompt.grounded_context["recommendation_run_id"] == "run-1"
    assert prompt.grounded_context["allowed_recommendation_ids"] == ["rec-1", "rec-2"]
    assert len(prompt.grounded_context["top_recommendations"]) == 2
    top_item = prompt.grounded_context["top_recommendations"][0]
    assert top_item["id"] == "rec-2"
    assert len(top_item["rationale_excerpt"]) <= 320


def test_prompt_appends_additional_recommendation_text_safely() -> None:
    prompt = build_seo_recommendation_narrative_prompt(
        run=_run(),
        recommendations=_recommendations(),
        by_status={"open": 1},
        by_category={"SEO": 1},
        by_severity={"WARNING": 1},
        by_effort_bucket={"LOW": 1},
        by_priority_band={"high": 1},
        backlog=_recommendations(),
        prompt_text_recommendation="Prefer concise operator language.",
    )

    assert "ADDITIONAL_RECOMMENDATION_TEXT" in prompt.user_prompt
    assert "Prefer concise operator language." in prompt.user_prompt


def test_prompt_is_deterministic_for_same_inputs() -> None:
    left = build_seo_recommendation_narrative_prompt(
        run=_run(),
        recommendations=_recommendations(),
        by_status={"open": 1, "in_progress": 1},
        by_category={"SEO": 1, "CONTENT": 1},
        by_severity={"CRITICAL": 1, "WARNING": 1},
        by_effort_bucket={"HIGH": 1, "LOW": 1},
        by_priority_band={"critical": 1, "high": 1},
        backlog=_recommendations(),
    )
    right = build_seo_recommendation_narrative_prompt(
        run=_run(),
        recommendations=_recommendations(),
        by_status={"open": 1, "in_progress": 1},
        by_category={"SEO": 1, "CONTENT": 1},
        by_severity={"CRITICAL": 1, "WARNING": 1},
        by_effort_bucket={"HIGH": 1, "LOW": 1},
        by_priority_band={"critical": 1, "high": 1},
        backlog=_recommendations(),
    )

    assert left.system_prompt == right.system_prompt
    assert left.user_prompt == right.user_prompt
    assert left.grounded_context == right.grounded_context
