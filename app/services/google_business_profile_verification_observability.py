from __future__ import annotations

from collections import Counter
from threading import Lock

_ALLOWED_EVENTS: frozenset[str] = frozenset(
    {
        "provider_state_unmapped",
        "provider_method_missing",
        "provider_method_unmapped",
        "provider_error_fallback",
        "option_token_invalid",
        "option_provider_method_unavailable",
        "option_destination_unavailable",
        "option_selected_method_unavailable",
        "verification_record_missing_fields",
        "guidance_fallback_unknown",
    }
)


class GoogleBusinessProfileVerificationObservability:
    """In-process counters for GBP verification normalization/guidance quality signals."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._lock = Lock()

    def increment(self, event: str) -> None:
        if event not in _ALLOWED_EVENTS:
            return
        with self._lock:
            self._counts[event] += 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counts)

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()


verification_observability = GoogleBusinessProfileVerificationObservability()


def record_gbp_verification_observation(event: str) -> None:
    verification_observability.increment(event)


def export_gbp_verification_counters() -> dict[str, int]:
    snapshot = verification_observability.snapshot()

    unknown_provider_state = snapshot.get("provider_state_unmapped", 0)
    unknown_provider_method = snapshot.get("provider_method_missing", 0) + snapshot.get("provider_method_unmapped", 0)
    provider_error_fallback = snapshot.get("provider_error_fallback", 0)
    invalid_option_token = snapshot.get("option_token_invalid", 0)
    unavailable_method_revalidation = snapshot.get("option_provider_method_unavailable", 0) + snapshot.get(
        "option_selected_method_unavailable", 0
    )
    unavailable_destination_revalidation = snapshot.get("option_destination_unavailable", 0)
    missing_expected_verification_fields = snapshot.get("verification_record_missing_fields", 0)
    guidance_fallback = snapshot.get("guidance_fallback_unknown", 0)

    # "mapping_gaps" is an aggregate quality signal over fallback/missing mapping paths.
    mapping_gaps = (
        unknown_provider_state
        + unknown_provider_method
        + provider_error_fallback
        + missing_expected_verification_fields
    )

    return {
        "unknown_provider_state": unknown_provider_state,
        "unknown_provider_method": unknown_provider_method,
        "provider_error_fallback": provider_error_fallback,
        "invalid_option_token": invalid_option_token,
        "unavailable_method_revalidation": unavailable_method_revalidation,
        "unavailable_destination_revalidation": unavailable_destination_revalidation,
        "missing_expected_verification_fields": missing_expected_verification_fields,
        "mapping_gaps": mapping_gaps,
        "guidance_fallback": guidance_fallback,
    }
