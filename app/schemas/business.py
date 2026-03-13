from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
