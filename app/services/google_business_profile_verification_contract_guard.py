from __future__ import annotations

import json
import re
from pathlib import Path
from typing import get_args

from fastapi.routing import APIRoute
from pydantic import BaseModel

from app.api.routes.integrations import router as integrations_router
from app.schemas.google_business_profile import (
    GoogleBusinessProfileCompleteVerificationResponse,
    GoogleBusinessProfileGuidanceCtaType,
    GoogleBusinessProfileGuidancePriority,
    GoogleBusinessProfileGuidanceRecommendedAction,
    GoogleBusinessProfileGuidanceVerificationState,
    GoogleBusinessProfileLocationVerificationResponse,
    GoogleBusinessProfileRetryVerificationResponse,
    GoogleBusinessProfileStartVerificationResponse,
    GoogleBusinessProfileVerificationActionRequired,
    GoogleBusinessProfileVerificationErrorCode,
    GoogleBusinessProfileVerificationErrorDetailResponse,
    GoogleBusinessProfileVerificationGuidanceResponse,
    GoogleBusinessProfileVerificationMethod,
    GoogleBusinessProfileVerificationMethodOptionResponse,
    GoogleBusinessProfileVerificationOptionsResponse,
    GoogleBusinessProfileVerificationStatusCurrentResponse,
    GoogleBusinessProfileVerificationStatusResponse,
    GoogleBusinessProfileVerificationWorkflowContractResponse,
    GoogleBusinessProfileVerificationWorkflowState,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_ARTIFACT_PATH = PROJECT_ROOT / "docs" / "contracts" / "gbp-verification-contract.schema.json"
DEFAULT_FRONTEND_TYPES_PATH = PROJECT_ROOT / "frontend" / "operator-ui" / "lib" / "api" / "types.ts"


_CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "GoogleBusinessProfileLocationVerificationResponse": GoogleBusinessProfileLocationVerificationResponse,
    "GoogleBusinessProfileVerificationGuidanceResponse": GoogleBusinessProfileVerificationGuidanceResponse,
    "GoogleBusinessProfileVerificationMethodOptionResponse": GoogleBusinessProfileVerificationMethodOptionResponse,
    "GoogleBusinessProfileVerificationStatusCurrentResponse": GoogleBusinessProfileVerificationStatusCurrentResponse,
    "GoogleBusinessProfileVerificationWorkflowContractResponse": (
        GoogleBusinessProfileVerificationWorkflowContractResponse
    ),
    "GoogleBusinessProfileVerificationStatusResponse": GoogleBusinessProfileVerificationStatusResponse,
    "GoogleBusinessProfileVerificationOptionsResponse": GoogleBusinessProfileVerificationOptionsResponse,
    "GoogleBusinessProfileStartVerificationResponse": GoogleBusinessProfileStartVerificationResponse,
    "GoogleBusinessProfileCompleteVerificationResponse": GoogleBusinessProfileCompleteVerificationResponse,
    "GoogleBusinessProfileRetryVerificationResponse": GoogleBusinessProfileRetryVerificationResponse,
    "GoogleBusinessProfileVerificationErrorDetailResponse": GoogleBusinessProfileVerificationErrorDetailResponse,
}

_CONTRACT_ENUMS: dict[str, tuple[str, ...]] = {
    "GoogleBusinessProfileVerificationWorkflowState": tuple(
        str(value) for value in get_args(GoogleBusinessProfileVerificationWorkflowState)
    ),
    "GoogleBusinessProfileVerificationActionRequired": tuple(
        str(value) for value in get_args(GoogleBusinessProfileVerificationActionRequired)
    ),
    "GoogleBusinessProfileVerificationMethod": tuple(
        str(value) for value in get_args(GoogleBusinessProfileVerificationMethod)
    ),
    "GoogleBusinessProfileVerificationErrorCode": tuple(
        str(value) for value in get_args(GoogleBusinessProfileVerificationErrorCode)
    ),
    "GoogleBusinessProfileGuidanceVerificationState": tuple(
        str(value) for value in get_args(GoogleBusinessProfileGuidanceVerificationState)
    ),
    "GoogleBusinessProfileGuidanceRecommendedAction": tuple(
        str(value) for value in get_args(GoogleBusinessProfileGuidanceRecommendedAction)
    ),
    "GoogleBusinessProfileGuidancePriority": tuple(
        str(value) for value in get_args(GoogleBusinessProfileGuidancePriority)
    ),
    "GoogleBusinessProfileGuidanceCtaType": tuple(
        str(value) for value in get_args(GoogleBusinessProfileGuidanceCtaType)
    ),
}

_EXPECTED_VERIFICATION_ROUTE_MODELS: dict[tuple[str, str], type[BaseModel]] = {
    (
        "GET",
        "/api/integrations/google/business-profile/locations/{location_id}/verification",
    ): GoogleBusinessProfileLocationVerificationResponse,
    (
        "GET",
        "/api/integrations/google/business-profile/locations/{location_id}/verification/options",
    ): GoogleBusinessProfileVerificationOptionsResponse,
    (
        "GET",
        "/api/integrations/google/business-profile/locations/{location_id}/verification/status",
    ): GoogleBusinessProfileVerificationStatusResponse,
    (
        "POST",
        "/api/integrations/google/business-profile/locations/{location_id}/verification/start",
    ): GoogleBusinessProfileStartVerificationResponse,
    (
        "POST",
        "/api/integrations/google/business-profile/locations/{location_id}/verification/complete",
    ): GoogleBusinessProfileCompleteVerificationResponse,
    (
        "POST",
        "/api/integrations/google/business-profile/locations/{location_id}/verification/retry",
    ): GoogleBusinessProfileRetryVerificationResponse,
}

_FRONTEND_EXPECTED_UNIONS: dict[str, tuple[str, ...]] = {
    "GoogleBusinessProfileVerificationWorkflowState": _CONTRACT_ENUMS["GoogleBusinessProfileVerificationWorkflowState"],
    "GoogleBusinessProfileVerificationActionRequired": _CONTRACT_ENUMS[
        "GoogleBusinessProfileVerificationActionRequired"
    ],
    "GoogleBusinessProfileVerificationMethod": _CONTRACT_ENUMS["GoogleBusinessProfileVerificationMethod"],
    "GoogleBusinessProfileVerificationErrorCode": _CONTRACT_ENUMS["GoogleBusinessProfileVerificationErrorCode"],
    "GoogleBusinessProfileGuidanceVerificationState": _CONTRACT_ENUMS["GoogleBusinessProfileGuidanceVerificationState"],
    "GoogleBusinessProfileGuidanceRecommendedAction": _CONTRACT_ENUMS["GoogleBusinessProfileGuidanceRecommendedAction"],
    "GoogleBusinessProfileGuidancePriority": _CONTRACT_ENUMS["GoogleBusinessProfileGuidancePriority"],
    "GoogleBusinessProfileGuidanceCtaType": _CONTRACT_ENUMS["GoogleBusinessProfileGuidanceCtaType"],
}

_FRONTEND_INTERFACE_FIELDS: dict[str, tuple[str, ...]] = {
    "GoogleBusinessProfileVerificationGuidance": (
        "title",
        "summary",
        "instructions",
        "tips",
        "warnings",
        "troubleshooting",
        "cta_type",
    ),
    "GoogleBusinessProfileVerificationWorkflowContract": (
        "location_id",
        "verification_state",
        "action_required",
        "message",
        "reconnect_required",
        "guidance",
    ),
    "GoogleBusinessProfileVerificationStatusResponse": (
        "current_verification",
        "available_methods",
    ),
    "GoogleBusinessProfileVerificationOptionsResponse": (
        "location_id",
        "current_verification_state",
        "methods",
        "guidance",
    ),
    "GoogleBusinessProfileVerificationActionResponse": (
        "verification_id",
        "expires_at",
        "status",
    ),
    "GoogleBusinessProfileVerificationErrorDetail": (
        "code",
        "message",
        "reconnect_required",
        "guidance",
    ),
}


def build_verification_contract_artifact() -> dict[str, object]:
    route_contract = [
        {
            "method": method,
            "path": path,
            "response_model": response_model.__name__,
        }
        for (method, path), response_model in sorted(_EXPECTED_VERIFICATION_ROUTE_MODELS.items())
    ]
    schema_contract = {
        name: model.model_json_schema(mode="serialization")
        for name, model in sorted(_CONTRACT_MODELS.items(), key=lambda item: item[0])
    }
    enum_contract = {name: list(values) for name, values in sorted(_CONTRACT_ENUMS.items(), key=lambda item: item[0])}
    return {
        "contract": "google_business_profile_verification",
        "version": 1,
        "schemas": schema_contract,
        "enums": enum_contract,
        "routes": route_contract,
    }


def render_verification_contract_artifact() -> str:
    return json.dumps(build_verification_contract_artifact(), indent=2, sort_keys=True) + "\n"


def write_verification_contract_artifact(path: Path = DEFAULT_CONTRACT_ARTIFACT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_verification_contract_artifact(), encoding="utf-8")


def validate_contract_artifact_is_current(path: Path = DEFAULT_CONTRACT_ARTIFACT_PATH) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"Contract artifact file is missing: {path}")
        return errors

    expected = render_verification_contract_artifact()
    current = path.read_text(encoding="utf-8")
    if current != expected:
        errors.append(
            "GBP verification contract artifact is stale. "
            "Regenerate with: python scripts/gbp_verification_contract_guard.py --write"
        )
    return errors


def validate_verification_route_response_models() -> list[str]:
    errors: list[str] = []
    route_lookup: dict[tuple[str, str], APIRoute] = {}

    for route in integrations_router.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted(route.methods or []):
            if method in {"HEAD", "OPTIONS"}:
                continue
            route_lookup[(method, route.path)] = route

    for key, expected_model in _EXPECTED_VERIFICATION_ROUTE_MODELS.items():
        route = route_lookup.get(key)
        method, path = key
        if route is None:
            errors.append(f"Missing verification route in integrations router: {method} {path}")
            continue
        if route.response_model is not expected_model:
            actual_name = getattr(route.response_model, "__name__", str(route.response_model))
            errors.append(
                f"Unexpected response model for {method} {path}: "
                f"expected={expected_model.__name__} actual={actual_name}"
            )
    return errors


def validate_frontend_contract_types(path: Path = DEFAULT_FRONTEND_TYPES_PATH) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Frontend contract file is missing: {path}"]

    content = path.read_text(encoding="utf-8")

    for alias, expected_values in sorted(_FRONTEND_EXPECTED_UNIONS.items(), key=lambda item: item[0]):
        actual_values = _extract_typescript_union_literals(content, alias)
        if actual_values is None:
            errors.append(f"Missing TypeScript union alias: {alias}")
            continue
        expected_set = set(expected_values)
        actual_set = set(actual_values)
        if actual_set != expected_set:
            errors.append(
                f"TypeScript union drift for {alias}: expected={sorted(expected_set)} actual={sorted(actual_set)}"
            )

    for interface_name, required_fields in sorted(_FRONTEND_INTERFACE_FIELDS.items(), key=lambda item: item[0]):
        interface_body = _extract_typescript_interface_body(content, interface_name)
        if interface_body is None:
            errors.append(f"Missing TypeScript interface: {interface_name}")
            continue
        for field_name in required_fields:
            field_pattern = rf"\b{re.escape(field_name)}\??\s*:"
            if re.search(field_pattern, interface_body) is None:
                errors.append(f"TypeScript interface {interface_name} is missing field: {field_name}")

    return errors


def run_verification_contract_guard(
    *,
    artifact_path: Path = DEFAULT_CONTRACT_ARTIFACT_PATH,
    frontend_types_path: Path = DEFAULT_FRONTEND_TYPES_PATH,
    check_artifact: bool = True,
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_verification_route_response_models())
    errors.extend(validate_frontend_contract_types(frontend_types_path))
    if check_artifact:
        errors.extend(validate_contract_artifact_is_current(artifact_path))
    return errors


def _extract_typescript_union_literals(content: str, alias_name: str) -> tuple[str, ...] | None:
    pattern = rf"export\s+type\s+{re.escape(alias_name)}\s*=\s*(?P<body>.*?);"
    match = re.search(pattern, content, flags=re.DOTALL)
    if match is None:
        return None
    values = re.findall(r'"([^"]+)"', match.group("body"))
    return tuple(values)


def _extract_typescript_interface_body(content: str, interface_name: str) -> str | None:
    pattern = rf"export\s+interface\s+{re.escape(interface_name)}[^\{{]*\{{(?P<body>.*?)\}}"
    match = re.search(pattern, content, flags=re.DOTALL)
    if match is None:
        return None
    return match.group("body")
