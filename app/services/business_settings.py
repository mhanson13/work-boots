from __future__ import annotations

import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.business import Business
from app.repositories.business_repository import BusinessRepository
from app.schemas.business import BusinessSettingsUpdateRequest

_EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)


class BusinessSettingsNotFoundError(ValueError):
    pass


class BusinessSettingsValidationError(ValueError):
    pass


class BusinessSettingsService:
    def __init__(self, *, session: Session, business_repository: BusinessRepository) -> None:
        self.session = session
        self.business_repository = business_repository

    def get(self, *, business_id: str) -> Business:
        business = self.business_repository.get(business_id)
        if not business:
            raise BusinessSettingsNotFoundError("Business not found")
        return business

    def update_settings(self, *, business_id: str, payload: BusinessSettingsUpdateRequest) -> Business:
        business = self.get(business_id=business_id)

        updates = payload.model_dump(exclude_unset=True)
        normalized_updates = self._normalize_updates(updates)
        effective = self._effective_settings(business=business, updates=normalized_updates)
        self._validate_effective_settings(effective)

        for field_name, value in normalized_updates.items():
            setattr(business, field_name, value)

        self.business_repository.save(business)
        self.session.commit()
        self.session.refresh(business)
        return business

    def _normalize_updates(self, updates: dict) -> dict:
        normalized = dict(updates)

        if "notification_email" in normalized:
            email_value = normalized["notification_email"]
            if email_value is None:
                normalized["notification_email"] = None
            else:
                email = str(email_value).strip().lower()
                if not _EMAIL_REGEX.match(email):
                    raise BusinessSettingsValidationError("notification_email must be a valid email address.")
                normalized["notification_email"] = email

        if "notification_phone" in normalized:
            phone_value = normalized["notification_phone"]
            if phone_value is None:
                normalized["notification_phone"] = None
            else:
                phone = self._normalize_us_phone(str(phone_value))
                if phone is None:
                    raise BusinessSettingsValidationError(
                        "notification_phone must be a valid US phone number (10 digits, optional country code)."
                    )
                normalized["notification_phone"] = phone

        if "timezone" in normalized:
            timezone_value = normalized["timezone"]
            if timezone_value is None:
                raise BusinessSettingsValidationError("timezone cannot be null.")
            timezone = str(timezone_value).strip()
            try:
                ZoneInfo(timezone)
            except ZoneInfoNotFoundError as exc:
                raise BusinessSettingsValidationError("timezone must be a valid IANA timezone.") from exc
            normalized["timezone"] = timezone

        return normalized

    def _effective_settings(self, *, business: Business, updates: dict) -> dict:
        return {
            "notification_phone": updates.get("notification_phone", business.notification_phone),
            "notification_email": updates.get("notification_email", business.notification_email),
            "sms_enabled": updates.get("sms_enabled", business.sms_enabled),
            "email_enabled": updates.get("email_enabled", business.email_enabled),
            "customer_auto_ack_enabled": updates.get(
                "customer_auto_ack_enabled", business.customer_auto_ack_enabled
            ),
            "contractor_alerts_enabled": updates.get(
                "contractor_alerts_enabled", business.contractor_alerts_enabled
            ),
            "timezone": updates.get("timezone", business.timezone),
        }

    def _validate_effective_settings(self, effective: dict) -> None:
        sms_enabled = bool(effective["sms_enabled"])
        email_enabled = bool(effective["email_enabled"])

        if sms_enabled and not self._is_valid_us_phone(effective["notification_phone"]):
            raise BusinessSettingsValidationError(
                "notification_phone is required and must be valid when sms_enabled is true."
            )

        if email_enabled and not self._is_valid_email(effective["notification_email"]):
            raise BusinessSettingsValidationError(
                "notification_email is required and must be valid when email_enabled is true."
            )

        if effective["contractor_alerts_enabled"] and not (sms_enabled or email_enabled):
            raise BusinessSettingsValidationError(
                "At least one channel (sms or email) must be enabled when contractor_alerts_enabled is true."
            )

        # Customer auto-ack uses the incoming lead's contact details plus enabled channels.
        # It does not depend on business notification targets, only channel availability.
        if effective["customer_auto_ack_enabled"] and not (sms_enabled or email_enabled):
            raise BusinessSettingsValidationError(
                "At least one channel (sms or email) must be enabled when customer_auto_ack_enabled is true."
            )

    def _is_valid_email(self, value: str | None) -> bool:
        if not value:
            return False
        return bool(_EMAIL_REGEX.match(value.strip()))

    def _is_valid_us_phone(self, value: str | None) -> bool:
        return self._normalize_us_phone(value) is not None

    def _normalize_us_phone(self, value: str | None) -> str | None:
        if not value:
            return None
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10:
            return None
        return f"+1{digits}"
