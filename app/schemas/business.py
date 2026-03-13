from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class BusinessSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    notification_phone: str | None
    notification_email: str | None
    sms_enabled: bool
    email_enabled: bool
    customer_auto_ack_enabled: bool
    contractor_alerts_enabled: bool
    timezone: str
    created_at: datetime
    updated_at: datetime


class BusinessSettingsUpdateRequest(BaseModel):
    notification_phone: str | None = None
    notification_email: str | None = None
    sms_enabled: bool | None = None
    email_enabled: bool | None = None
    customer_auto_ack_enabled: bool | None = None
    contractor_alerts_enabled: bool | None = None
    timezone: str | None = None

    @field_validator("notification_phone", "notification_email", "timezone", mode="before")
    @classmethod
    def normalize_optional_text_fields(cls, value):
        return _clean_optional_text(value)


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    return cleaned
