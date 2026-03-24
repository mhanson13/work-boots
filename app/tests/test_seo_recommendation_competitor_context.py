from __future__ import annotations

from app.services.seo_recommendation_competitor_context import (
    extract_recommendation_competitor_context,
)


def test_extract_recommendation_competitor_context_with_signal() -> None:
    context = extract_recommendation_competitor_context(
        {
            "top_opportunities": [
                " Expand service pages ",
                "Expand service pages",
                "Improve local proof",
            ],
            "summary": "  Competitors rank for nearby emergency keywords.  ",
            "competitors": [
                {"name": "  Alpha Plumbing "},
                {"name": "alpha plumbing"},
                {"name": "Beta HVAC"},
                {"name": "Unknown"},
            ],
        }
    )

    assert context == {
        "top_opportunities": ["Expand service pages", "Improve local proof"],
        "competitor_summary": "Competitors rank for nearby emergency keywords.",
        "competitor_names": ["Alpha Plumbing", "Beta HVAC"],
    }


def test_extract_recommendation_competitor_context_missing_payload_is_safe() -> None:
    assert extract_recommendation_competitor_context(None) == {
        "top_opportunities": [],
        "competitor_summary": "",
        "competitor_names": [],
    }


def test_extract_recommendation_competitor_context_partial_payload_is_safe() -> None:
    context = extract_recommendation_competitor_context(
        {
            "top_opportunities": [None, "  ", "Improve trust signals"],
            "competitors": [{}, {"name": "  "}],
            "summary": None,
        }
    )

    assert context == {
        "top_opportunities": ["Improve trust signals"],
        "competitor_summary": "",
        "competitor_names": [],
    }


def test_extract_recommendation_competitor_context_bounds_lists() -> None:
    context = extract_recommendation_competitor_context(
        {
            "top_opportunities": [f"Opportunity {idx}" for idx in range(1, 12)],
            "competitors": [{"name": f"Competitor {idx}"} for idx in range(1, 12)],
            "summary": "Summary",
        }
    )

    assert len(context["top_opportunities"]) == 5
    assert context["top_opportunities"] == [
        "Opportunity 1",
        "Opportunity 2",
        "Opportunity 3",
        "Opportunity 4",
        "Opportunity 5",
    ]
    assert len(context["competitor_names"]) == 5
    assert context["competitor_names"] == [
        "Competitor 1",
        "Competitor 2",
        "Competitor 3",
        "Competitor 4",
        "Competitor 5",
    ]


def test_extract_recommendation_competitor_context_ignores_normalizer_fallback() -> None:
    context = extract_recommendation_competitor_context(
        {
            "top_opportunities": [
                "Improve website clarity",
                "Add trust signals",
                "Clarify services",
            ],
            "summary": "Competitor analysis unavailable, using fallback insights.",
            "competitors": [],
        }
    )

    assert context == {
        "top_opportunities": [],
        "competitor_summary": "",
        "competitor_names": [],
    }
