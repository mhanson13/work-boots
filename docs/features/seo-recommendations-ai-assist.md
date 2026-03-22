# SEO Recommendations (Deterministic + AI Narrative)

## Overview
This feature produces deterministic SEO recommendations from persisted audit/comparison evidence, then optionally generates an AI narrative over those persisted recommendation artifacts.

Deterministic recommendation records remain canonical. AI output is advisory explanation only.

## Why This Exists
- Deterministic rules provide stable, auditable recommendation artifacts.
- Operators still need fast, human-readable context on priorities and backlog.
- AI narrative generation improves explainability without turning AI into the source of truth.

## Architecture / Flow
1. Deterministic run creation:
   - `POST /api/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs`
   - Service reads persisted lineage inputs (`audit_run_id`, `comparison_run_id`) and generates deterministic recommendations.
2. Persistence:
   - Run stored in `seo_recommendation_runs`
   - Recommendation rows stored in `seo_recommendations`
3. AI narrative generation (manual trigger or automation step):
   - `POST /api/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives`
   - Prompt is built from persisted recommendation artifacts and rollups.
   - Provider output is schema-validated before persistence.
4. Narrative retrieval:
   - list/latest/by-id narrative endpoints return persisted narrative versions.
5. UI:
   - Recommendation queue and run detail pages render deterministic recommendation data.
   - Narrative views render AI explanation when available.

## Data Model
- `seo_recommendation_runs`: deterministic run lineage/status/rollups.
- `seo_recommendations`: deterministic recommendation artifacts and workflow fields.
- `seo_recommendation_narratives`: versioned narrative records with:
  - `status` (`completed` or `failed`)
  - `narrative_text`
  - `top_themes_json`
  - `sections_json`
  - `provider_name`, `model_name`, `prompt_version`
  - `error_message`

## Key Constraints / Invariants
- AI never creates canonical recommendation artifacts.
- AI never mutates business settings or workflow state.
- Narrative generation is grounded in persisted recommendation artifacts only.
- Business/site scoping is enforced in routes, services, and repositories.

## Configuration
AI narrative provider wiring uses existing AI runtime settings:
- `AI_PROVIDER_API_KEY` (secret; required for OpenAI in production/staging)
- `AI_PROVIDER_NAME` (`openai` or `mock`)
- `AI_MODEL_NAME` (default `gpt-4o-mini`)
- `AI_TIMEOUT_VALUE` (default `30`)
- `AI_PROMPT_TEXT_RECOMMENDATION` (optional supplemental recommendation text)
- `OPENAI_API_BASE_URL` (default `https://api.openai.com/v1`)

Behavior:
- `openai` + valid key -> real provider.
- `openai` + missing key in local/test/dev -> mock fallback for local workflows/tests.
- `openai` + missing key in production/staging -> safe misconfigured-provider failure.

## Operational Behavior
- Narrative generation is versioned per recommendation run.
- Provider failures persist a `failed` narrative version with safe `error_message`.
- Failure isolation: recommendation run/recommendation records are not mutated by narrative failures.
- Provider/model/prompt metadata is persisted for auditability.

## Failure Modes
- Timeout/provider request/auth/config/schema/parse failures are normalized to safe errors.
- API returns validation-safe failures (`422`) for narrative generation failures.
- Existing deterministic recommendation artifacts remain available even if narrative generation fails.

## Security Considerations
- Raw provider credentials are not exposed in API responses.
- Prompt context is treated as data; output is schema-validated before persistence.
- AI output remains advisory and cannot bypass review/workflow controls.

## Future Extensions
- Provider expansion behind the existing provider abstraction.
- Richer grounded narrative sections (still tied to deterministic IDs/rollups).
- Additional observability for narrative generation latency/error categories.
