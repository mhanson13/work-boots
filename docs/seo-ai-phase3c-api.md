# SEO.ai Phase 3C API

## Architecture Contract
- business-scoped and site-scoped routes
- manual-trigger narrative generation
- AI narrative generation over persisted recommendation artifacts only
- no AI recommendation generation or workflow mutation

Primary route prefixes:
- `/api/businesses/{business_id}/seo/...`
- `/api/v1/businesses/{business_id}/seo/...` (site-scoped compatibility)

## Endpoints

## Create recommendation narrative
`POST /api/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives`
and
`POST /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives`

Behavior:
- creates next narrative version for the recommendation run
- persists `completed` on success
- persists `failed` with `error_message` on provider failure
- validates AI output against a strict structured schema before persistence

Response:
- `SEORecommendationNarrativeRead`

## List recommendation narratives
`GET /api/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives`
and
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives`

Response:
- `SEORecommendationNarrativeListResponse`

## Get latest recommendation narrative
`GET /api/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives/latest`
and
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/narratives/latest`

Response:
- `SEORecommendationNarrativeRead`

## Get recommendation narrative by id
`GET /api/businesses/{business_id}/seo/sites/{site_id}/recommendation-narratives/{narrative_id}`
and
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-narratives/{narrative_id}`

Response:
- `SEORecommendationNarrativeRead`

## Narrative response fields
Narrative resources expose:
- `id`
- `recommendation_run_id`
- `version`
- `status`
- `provider_name`
- `model_name`
- `prompt_version`
- `narrative_text`
- `top_themes_json`
- `sections_json`
- `error_message`
- timestamps and actor metadata

## Status and Error Semantics
- `404` for out-of-scope business/site/run/narrative access
- `422` for invalid run state or provider generation failure
- provider/runtime errors are normalized to safe messages (no credential leakage)

## Grounding and Deterministic Authority
Narratives are explanatory overlays for persisted deterministic recommendations.

Authoritative recommendation state remains in persisted recommendation records and workflow metadata.
