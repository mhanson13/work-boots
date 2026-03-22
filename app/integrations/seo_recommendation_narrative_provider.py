from __future__ import annotations

from dataclasses import dataclass
import json
import socket
import urllib.error
import urllib.request

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.integrations.seo_summary_provider import SEORecommendationNarrativeOutput
from app.models.seo_recommendation import SEORecommendation
from app.models.seo_recommendation_run import SEORecommendationRun
from app.services.seo_recommendation_narrative_prompt import (
    SEO_RECOMMENDATION_NARRATIVE_PROMPT_VERSION,
    build_seo_recommendation_narrative_prompt,
)


_PROVIDER_ERROR_TIMEOUT = "timeout"
_PROVIDER_ERROR_AUTH_CONFIG = "provider_auth_config"
_PROVIDER_ERROR_INVALID_OUTPUT = "invalid_output"
_PROVIDER_ERROR_SCHEMA_VALIDATION = "schema_validation"
_PROVIDER_ERROR_PARSING = "parsing_error"
_PROVIDER_ERROR_REQUEST = "provider_request"

_MAX_NARRATIVE_TEXT_LENGTH = 6000
_MAX_THEME_LENGTH = 140
_MAX_THEMES = 8
_MAX_SECTION_TEXT_LENGTH = 1200
_MAX_NEXT_ACTION_LENGTH = 220
_MAX_NEXT_ACTIONS = 10
_MAX_RECOMMENDATION_REFERENCES = 25


@dataclass(frozen=True)
class SEORecommendationNarrativeProviderError(RuntimeError):
    code: str
    safe_message: str
    provider_name: str
    model_name: str
    prompt_version: str
    raw_output: str | None = None

    def __str__(self) -> str:
        return self.safe_message


class MisconfiguredSEORecommendationNarrativeProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        model_name: str,
        prompt_version: str,
        safe_message: str,
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.safe_message = safe_message

    def generate_narrative(
        self,
        *,
        run: SEORecommendationRun,
        recommendations: list[SEORecommendation],
        by_status: dict[str, int],
        by_category: dict[str, int],
        by_severity: dict[str, int],
        by_effort_bucket: dict[str, int],
        by_priority_band: dict[str, int],
        backlog: list[SEORecommendation],
    ) -> SEORecommendationNarrativeOutput:
        del run, recommendations, by_status, by_category, by_severity, by_effort_bucket, by_priority_band, backlog
        raise SEORecommendationNarrativeProviderError(
            code=_PROVIDER_ERROR_AUTH_CONFIG,
            safe_message=self.safe_message,
            provider_name=self.provider_name,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
        )


class OpenAISEORecommendationNarrativeProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: int = 30,
        api_base_url: str = "https://api.openai.com/v1",
        prompt_version: str = SEO_RECOMMENDATION_NARRATIVE_PROMPT_VERSION,
        prompt_text_recommendation: str = "",
    ) -> None:
        normalized_key = api_key.strip()
        if not normalized_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = normalized_key
        self.model_name = model_name.strip() or "gpt-4o-mini"
        self.timeout_seconds = max(1, int(timeout_seconds))
        self.api_base_url = api_base_url.rstrip("/")
        self.prompt_version = prompt_version.strip() or SEO_RECOMMENDATION_NARRATIVE_PROMPT_VERSION
        self.prompt_text_recommendation = prompt_text_recommendation

    def generate_narrative(
        self,
        *,
        run: SEORecommendationRun,
        recommendations: list[SEORecommendation],
        by_status: dict[str, int],
        by_category: dict[str, int],
        by_severity: dict[str, int],
        by_effort_bucket: dict[str, int],
        by_priority_band: dict[str, int],
        backlog: list[SEORecommendation],
    ) -> SEORecommendationNarrativeOutput:
        prompt = build_seo_recommendation_narrative_prompt(
            run=run,
            recommendations=recommendations,
            by_status=by_status,
            by_category=by_category,
            by_severity=by_severity,
            by_effort_bucket=by_effort_bucket,
            by_priority_band=by_priority_band,
            backlog=backlog,
            prompt_version=self.prompt_version,
            prompt_text_recommendation=self.prompt_text_recommendation,
        )
        payload = self._build_request_payload(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
        )
        raw_response = self._request_completion(payload)
        response_json = self._parse_json_object(
            raw_response,
            code=_PROVIDER_ERROR_PARSING,
            safe_message="Recommendation narrative response could not be parsed.",
        )
        assistant_content = self._extract_assistant_content(response_json)
        structured_json = self._parse_json_object(
            assistant_content,
            code=_PROVIDER_ERROR_INVALID_OUTPUT,
            safe_message="Recommendation narrative returned malformed output.",
            raw_output=assistant_content,
        )
        try:
            parsed = _OpenAIRecommendationNarrativeResponse.model_validate(structured_json)
        except ValidationError as exc:
            raise self._provider_error(
                code=_PROVIDER_ERROR_SCHEMA_VALIDATION,
                safe_message="Recommendation narrative returned invalid structured output.",
                raw_output=assistant_content,
            ) from exc

        model_name = _clean_optional_value(response_json.get("model")) or self.model_name
        allowed_ids = {
            _clean_optional_value(getattr(item, "id", None))
            for item in recommendations
        }
        allowed_recommendation_ids = {item for item in allowed_ids if item}

        sections = self._normalize_sections(
            parsed.sections,
            allowed_recommendation_ids=allowed_recommendation_ids,
            by_status=by_status,
            by_category=by_category,
            by_severity=by_severity,
            by_effort_bucket=by_effort_bucket,
            by_priority_band=by_priority_band,
        )
        return SEORecommendationNarrativeOutput(
            narrative_text=self._normalize_narrative_text(parsed.narrative_text),
            top_themes=self._normalize_top_themes(parsed.top_themes),
            sections=sections,
            provider_name=self.provider_name,
            model_name=model_name,
            prompt_version=prompt.prompt_version,
        )

    def _request_completion(self, payload: dict[str, object]) -> str:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self.api_base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            if exc.code in {401, 403}:
                raise self._provider_error(
                    code=_PROVIDER_ERROR_AUTH_CONFIG,
                    safe_message=(
                        "AI provider authentication failed. Verify recommendation narrative provider credentials."
                    ),
                    raw_output=body_text,
                ) from exc
            if exc.code in {408, 504}:
                raise self._provider_error(
                    code=_PROVIDER_ERROR_TIMEOUT,
                    safe_message="Recommendation narrative generation timed out while calling the AI provider.",
                    raw_output=body_text,
                ) from exc
            raise self._provider_error(
                code=_PROVIDER_ERROR_REQUEST,
                safe_message="Recommendation narrative provider request failed.",
                raw_output=body_text,
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise self._provider_error(
                code=_PROVIDER_ERROR_TIMEOUT,
                safe_message="Recommendation narrative generation timed out while calling the AI provider.",
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError) or isinstance(exc.reason, socket.timeout):
                raise self._provider_error(
                    code=_PROVIDER_ERROR_TIMEOUT,
                    safe_message="Recommendation narrative generation timed out while calling the AI provider.",
                ) from exc
            raise self._provider_error(
                code=_PROVIDER_ERROR_REQUEST,
                safe_message="Recommendation narrative provider request failed.",
            ) from exc

    def _build_request_payload(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, object]:
        return {
            "model": self.model_name,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "seo_recommendation_narrative_response",
                    "strict": True,
                    "schema": _build_narrative_json_schema(),
                },
            },
        }

    def _extract_assistant_content(self, response_json: dict[str, object]) -> str:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise self._provider_error(
                code=_PROVIDER_ERROR_PARSING,
                safe_message="Recommendation narrative response did not include choices.",
                raw_output=json.dumps(response_json, ensure_ascii=True, sort_keys=True),
            )
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise self._provider_error(
                code=_PROVIDER_ERROR_PARSING,
                safe_message="Recommendation narrative response choice was malformed.",
                raw_output=json.dumps(response_json, ensure_ascii=True, sort_keys=True),
            )
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise self._provider_error(
                code=_PROVIDER_ERROR_PARSING,
                safe_message="Recommendation narrative response message was malformed.",
                raw_output=json.dumps(response_json, ensure_ascii=True, sort_keys=True),
            )
        content = message.get("content")
        if isinstance(content, str):
            normalized = content.strip()
            if normalized:
                return normalized
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
            if parts:
                return "\n".join(parts)
        raise self._provider_error(
            code=_PROVIDER_ERROR_PARSING,
            safe_message="Recommendation narrative response did not include content.",
            raw_output=json.dumps(response_json, ensure_ascii=True, sort_keys=True),
        )

    def _parse_json_object(
        self,
        raw_json: str,
        *,
        code: str,
        safe_message: str,
        raw_output: str | None = None,
    ) -> dict[str, object]:
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise self._provider_error(
                code=code,
                safe_message=safe_message,
                raw_output=raw_output or raw_json,
            ) from exc
        if not isinstance(parsed, dict):
            raise self._provider_error(
                code=code,
                safe_message=safe_message,
                raw_output=raw_output or raw_json,
            )
        return parsed

    def _normalize_narrative_text(self, value: str) -> str:
        normalized = _clean_optional_value(value) or "No narrative text returned."
        if len(normalized) > _MAX_NARRATIVE_TEXT_LENGTH:
            return normalized[:_MAX_NARRATIVE_TEXT_LENGTH]
        return normalized

    def _normalize_top_themes(self, values: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in values:
            normalized = _clean_optional_value(item)
            if not normalized:
                continue
            if len(normalized) > _MAX_THEME_LENGTH:
                normalized = normalized[:_MAX_THEME_LENGTH]
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(normalized)
            if len(deduped) >= _MAX_THEMES:
                break
        return deduped

    def _normalize_sections(
        self,
        sections: _OpenAIRecommendationNarrativeSections | None,
        *,
        allowed_recommendation_ids: set[str],
        by_status: dict[str, int],
        by_category: dict[str, int],
        by_severity: dict[str, int],
        by_effort_bucket: dict[str, int],
        by_priority_band: dict[str, int],
    ) -> dict[str, object]:
        summary = _clean_optional_value(sections.summary if sections is not None else None)
        priority_rationale = _clean_optional_value(sections.priority_rationale if sections is not None else None)
        if summary and len(summary) > _MAX_SECTION_TEXT_LENGTH:
            summary = summary[:_MAX_SECTION_TEXT_LENGTH]
        if priority_rationale and len(priority_rationale) > _MAX_SECTION_TEXT_LENGTH:
            priority_rationale = priority_rationale[:_MAX_SECTION_TEXT_LENGTH]

        next_actions: list[str] = []
        references: list[str] = []
        if sections is not None:
            for value in sections.next_actions:
                normalized = _clean_optional_value(value)
                if not normalized:
                    continue
                if len(normalized) > _MAX_NEXT_ACTION_LENGTH:
                    normalized = normalized[:_MAX_NEXT_ACTION_LENGTH]
                if normalized not in next_actions:
                    next_actions.append(normalized)
                if len(next_actions) >= _MAX_NEXT_ACTIONS:
                    break

            for value in sections.recommendation_references:
                normalized = _clean_optional_value(value)
                if not normalized:
                    continue
                if normalized not in allowed_recommendation_ids:
                    continue
                if normalized not in references:
                    references.append(normalized)
                if len(references) >= _MAX_RECOMMENDATION_REFERENCES:
                    break

        return {
            "summary": summary,
            "priority_rationale": priority_rationale,
            "next_actions": next_actions,
            "recommendation_references": references,
            "status_rollup": _normalize_int_map(by_status),
            "category_rollup": _normalize_int_map(by_category),
            "severity_rollup": _normalize_int_map(by_severity),
            "effort_rollup": _normalize_int_map(by_effort_bucket),
            "priority_band_rollup": _normalize_int_map(by_priority_band),
        }

    def _provider_error(
        self,
        *,
        code: str,
        safe_message: str,
        raw_output: str | None = None,
    ) -> SEORecommendationNarrativeProviderError:
        return SEORecommendationNarrativeProviderError(
            code=code,
            safe_message=safe_message,
            provider_name=self.provider_name,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            raw_output=raw_output,
        )


class _OpenAIRecommendationNarrativeSections(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str | None = None
    priority_rationale: str | None = None
    next_actions: list[str] = Field(default_factory=list, max_length=_MAX_NEXT_ACTIONS)
    recommendation_references: list[str] = Field(default_factory=list, max_length=_MAX_RECOMMENDATION_REFERENCES)

    @field_validator("summary", "priority_rationale", mode="before")
    @classmethod
    def _normalize_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("next_actions", mode="before")
    @classmethod
    def _normalize_actions_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("next_actions must be a list")
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    @field_validator("recommendation_references", mode="before")
    @classmethod
    def _normalize_references_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("recommendation_references must be a list")
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized


class _OpenAIRecommendationNarrativeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    narrative_text: str
    top_themes: list[str] = Field(default_factory=list, max_length=_MAX_THEMES)
    sections: _OpenAIRecommendationNarrativeSections | None = None

    @field_validator("narrative_text", mode="before")
    @classmethod
    def _normalize_narrative_text(cls, value: object) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("narrative_text is required")
        return normalized

    @field_validator("top_themes", mode="before")
    @classmethod
    def _normalize_top_themes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("top_themes must be a list")
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized


def _build_narrative_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["narrative_text", "top_themes", "sections"],
        "properties": {
            "narrative_text": {"type": "string"},
            "top_themes": {
                "type": "array",
                "maxItems": _MAX_THEMES,
                "items": {"type": "string"},
            },
            "sections": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "required": [
                    "summary",
                    "priority_rationale",
                    "next_actions",
                    "recommendation_references",
                ],
                "properties": {
                    "summary": {"type": ["string", "null"]},
                    "priority_rationale": {"type": ["string", "null"]},
                    "next_actions": {
                        "type": "array",
                        "maxItems": _MAX_NEXT_ACTIONS,
                        "items": {"type": "string"},
                    },
                    "recommendation_references": {
                        "type": "array",
                        "maxItems": _MAX_RECOMMENDATION_REFERENCES,
                        "items": {"type": "string"},
                    },
                },
            },
        },
    }


def _normalize_int_map(raw: dict[str, int]) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for key, value in sorted(raw.items()):
        if not isinstance(key, str):
            continue
        clean_key = _clean_optional_value(key)
        if not clean_key:
            continue
        try:
            normalized[clean_key] = int(value)
        except (TypeError, ValueError):
            continue
    return normalized


def _clean_optional_value(value: object) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split()).strip()
    return normalized or None
