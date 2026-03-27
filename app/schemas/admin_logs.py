from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class GCPLogsQueryRequest(BaseModel):
    filter: str = Field(..., min_length=1, max_length=5000)
    page_size: int | None = Field(default=None, ge=1, le=100)
    page_token: str | None = Field(default=None, max_length=2048)

    @field_validator("filter", mode="before")
    @classmethod
    def normalize_filter(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("filter is required.")
        return normalized

    @field_validator("page_token", mode="before")
    @classmethod
    def normalize_page_token(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        return normalized


class GCPLogEntryRead(BaseModel):
    timestamp: str | None = None
    severity: str | None = None
    log_name: str | None = None
    resource_type: str | None = None
    labels: dict[str, str] | None = None
    resource_labels: dict[str, str] | None = None
    insert_id: str | None = None
    text_payload_summary: str | None = None
    json_payload_summary: str | None = None
    proto_payload_summary: str | None = None


class GCPLogsQueryResponse(BaseModel):
    entries: list[GCPLogEntryRead]
    next_page_token: str | None = None
    page_size: int
    order_by: str
    resource_scope: list[str]


class ADCRuntimeCheckResponse(BaseModel):
    adc_available: bool
    project_id: str | None = None
    error: str | None = None
    phase: str | None = None
    cause_class: str | None = None
    credentials_class: str | None = None
