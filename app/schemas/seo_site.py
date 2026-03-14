from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SEOSiteCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    base_url: str = Field(min_length=1, max_length=2048)
    industry: str | None = Field(default=None, max_length=128)
    primary_location: str | None = Field(default=None, max_length=255)
    service_areas: list[str] | None = None
    is_active: bool = True
    is_primary: bool = False


class SEOSiteUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: str | None = Field(default=None, min_length=1, max_length=2048)
    industry: str | None = Field(default=None, max_length=128)
    primary_location: str | None = Field(default=None, max_length=255)
    service_areas: list[str] | None = None
    is_active: bool | None = None
    is_primary: bool | None = None


class SEOSiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    business_id: str
    display_name: str
    base_url: str
    normalized_domain: str
    industry: str | None
    primary_location: str | None
    service_areas_json: list[str] | None
    is_active: bool
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class SEOSiteListResponse(BaseModel):
    items: list[SEOSiteRead]
    total: int
