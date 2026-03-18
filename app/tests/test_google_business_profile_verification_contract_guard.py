from __future__ import annotations

from app.services.google_business_profile_verification_contract_guard import (
    build_verification_contract_artifact,
    run_verification_contract_guard,
    validate_contract_artifact_is_current,
)


def test_verification_contract_guard_has_no_route_or_frontend_drift() -> None:
    errors = run_verification_contract_guard(check_artifact=False)
    assert errors == []


def test_verification_contract_artifact_is_current() -> None:
    errors = validate_contract_artifact_is_current()
    assert errors == []


def test_verification_contract_artifact_contains_core_models() -> None:
    artifact = build_verification_contract_artifact()
    schemas = artifact["schemas"]
    assert isinstance(schemas, dict)
    assert "GoogleBusinessProfileVerificationStatusResponse" in schemas
    assert "GoogleBusinessProfileStartVerificationResponse" in schemas
    assert "GoogleBusinessProfileVerificationErrorDetailResponse" in schemas
