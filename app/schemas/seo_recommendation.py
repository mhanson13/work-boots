from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SEORecommendationRunStatus = Literal["queued", "running", "completed", "failed"]
SEORecommendationCategory = Literal["SEO", "CONTENT", "STRUCTURE", "TECHNICAL"]
SEORecommendationSeverity = Literal["INFO", "WARNING", "CRITICAL"]
SEORecommendationEffort = Literal["LOW", "MEDIUM", "HIGH"]

_CATEGORIES = {"SEO", "CONTENT", "STRUCTURE", "TECHNICAL"}
_SEVERITIES = {"INFO", "WARNING", "CRITICAL"}
_EFFORT_BUCKETS = {"LOW", "MEDIUM", "HIGH"}


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_int_map(raw: Any) -> dict[str, int]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise TypeError("Expected object for count map")
    normalized: dict[str, int] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        try:
            normalized[key] = int(value)
        except (TypeError, ValueError):
            continue
    return normalized


def _normalize_category(value: Any) -> SEORecommendationCategory:
    normalized = str(value or "").strip().upper()
    if normalized not in _CATEGORIES:
        return "TECHNICAL"
    return normalized  # type: ignore[return-value]


def _normalize_severity(value: Any) -> SEORecommendationSeverity:
    normalized = str(value or "").strip().upper()
    if normalized not in _SEVERITIES:
        return "INFO"
    return normalized  # type: ignore[return-value]


def _normalize_effort(value: Any) -> SEORecommendationEffort:
    normalized = str(value or "").strip().upper()
    if normalized not in _EFFORT_BUCKETS:
        return "MEDIUM"
    return normalized  # type: ignore[return-value]


class SEORecommendationRunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_run_id: str | None = Field(default=None, min_length=1, max_length=36)
    comparison_run_id: str | None = Field(default=None, min_length=1, max_length=36)

    @field_validator("audit_run_id", "comparison_run_id", mode="before")
    @classmethod
    def normalize_optional_ids(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _strip_or_none(str(value))

    @model_validator(mode="after")
    def require_at_least_one_lineage_reference(self) -> "SEORecommendationRunCreateRequest":
        if self.audit_run_id is None and self.comparison_run_id is None:
            raise ValueError("At least one of audit_run_id or comparison_run_id is required")
        return self


class SEORecommendationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    site_id: str
    audit_run_id: str | None
    comparison_run_id: str | None
    status: SEORecommendationRunStatus
    total_recommendations: int
    critical_recommendations: int
    warning_recommendations: int
    info_recommendations: int
    category_counts_json: dict[str, int] = Field(default_factory=dict)
    effort_bucket_counts_json: dict[str, int] = Field(default_factory=dict)
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error_summary: str | None
    created_by_principal_id: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("category_counts_json", "effort_bucket_counts_json", mode="before")
    @classmethod
    def normalize_count_maps(cls, value: Any) -> dict[str, int]:
        return _normalize_int_map(value)


class SEORecommendationRunListResponse(BaseModel):
    items: list[SEORecommendationRunRead]
    total: int


class SEORecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    site_id: str
    recommendation_run_id: str
    audit_run_id: str | None
    comparison_run_id: str | None
    rule_key: str
    category: SEORecommendationCategory
    severity: SEORecommendationSeverity
    title: str
    rationale: str
    priority_score: int
    effort_bucket: SEORecommendationEffort
    evidence_json: dict[str, object] | None
    created_at: datetime
    updated_at: datetime

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_field(cls, value: Any) -> SEORecommendationCategory:
        return _normalize_category(value)

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity_field(cls, value: Any) -> SEORecommendationSeverity:
        return _normalize_severity(value)

    @field_validator("effort_bucket", mode="before")
    @classmethod
    def normalize_effort_field(cls, value: Any) -> SEORecommendationEffort:
        return _normalize_effort(value)


class SEORecommendationListResponse(BaseModel):
    items: list[SEORecommendationRead]
    total: int
    by_category: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_effort_bucket: dict[str, int] = Field(default_factory=dict)


class SEORecommendationRunReportRead(BaseModel):
    recommendation_run: SEORecommendationRunRead
    rollups: dict[str, dict[str, int]]
    recommendations: SEORecommendationListResponse
