from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SEOAuditSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    site_id: str
    audit_run_id: str
    version: int
    status: str
    overall_health_summary: str | None
    top_issues_json: list[str] | None
    top_priorities_json: list[str] | None
    plain_english_explanation: str | None
    model_name: str
    prompt_version: str
    error_summary: str | None
    created_by_principal_id: str | None
    created_at: datetime
    updated_at: datetime
