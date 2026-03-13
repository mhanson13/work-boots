from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import ParsedLeadData


@dataclass(frozen=True)
class DeduplicationMatch:
    lead: Lead
    rule: str


class LeadDeduplicationService:
    def __init__(self, lead_repository: LeadRepository) -> None:
        self.lead_repository = lead_repository

    def find_duplicate(
        self,
        *,
        business_id: str,
        submitted_at: datetime,
        customer_name: str | None,
        phone: str | None,
        email: str | None,
    ) -> DeduplicationMatch | None:
        lookback_start = submitted_at - timedelta(days=7)
        candidates = self.lead_repository.list_recent_since(
            business_id=business_id,
            submitted_after=lookback_start,
        )

        input_phone = self._phone_key(phone)
        input_email = self._email_key(email)
        input_name = self._name_key(customer_name)

        # Highest-confidence signal: same name + phone on the same date.
        if input_phone and input_name:
            for lead in candidates:
                if (
                    self._phone_key(lead.phone) == input_phone
                    and self._name_key(lead.customer_name) == input_name
                    and lead.submitted_at.date() == submitted_at.date()
                ):
                    return DeduplicationMatch(lead=lead, rule="same_name_phone_same_day")

        if input_phone:
            for lead in candidates:
                if self._phone_key(lead.phone) == input_phone:
                    return DeduplicationMatch(lead=lead, rule="same_phone_7d")

        if input_email:
            for lead in candidates:
                if self._email_key(lead.email) == input_email:
                    return DeduplicationMatch(lead=lead, rule="same_email_7d")

        return None

    def merge_duplicate(self, *, lead: Lead, parsed: ParsedLeadData) -> list[str]:
        updated_fields: list[str] = []
        field_pairs = [
            ("customer_name", parsed.customer_name),
            ("phone", parsed.phone),
            ("email", parsed.email),
            ("service_type", parsed.service_type),
            ("city", parsed.city),
        ]

        for field_name, incoming_value in field_pairs:
            if not incoming_value:
                continue
            current_value = getattr(lead, field_name)
            if not current_value:
                setattr(lead, field_name, incoming_value)
                updated_fields.append(field_name)

        if parsed.message and parsed.message != lead.message:
            if not lead.message:
                lead.message = parsed.message
            else:
                lead.message = (
                    f"{lead.message}\n\n---\nFollow-up message ({parsed.submitted_at.isoformat()}): {parsed.message}"
                )
            updated_fields.append("message")

        if parsed.source_ref and not lead.source_ref:
            lead.source_ref = parsed.source_ref
            updated_fields.append("source_ref")

        return updated_fields

    def _phone_key(self, value: str | None) -> str | None:
        if not value:
            return None
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) >= 10:
            return digits[-10:]
        return digits or None

    def _email_key(self, value: str | None) -> str | None:
        return value.strip().lower() if value else None

    def _name_key(self, value: str | None) -> str | None:
        if not value:
            return None
        return re.sub(r"\s+", " ", value.strip().lower()) or None
