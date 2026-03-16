# SEO.ai Phase 3A API

## Architecture Contract
- business-scoped routes
- deterministic inputs only (persisted audit/comparison artifacts)
- no AI recommendation generation in Phase 3A

Primary route prefixes:
- `/api/businesses/{business_id}/seo/...`
- `/api/v1/businesses/{business_id}/seo/...` (site-scoped compatibility surface)

## Endpoints

## Create recommendation run
`POST /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs`

Request:
```json
{
  "audit_run_id": "optional-uuid",
  "comparison_run_id": "optional-uuid"
}
```

Validation:
- at least one lineage ID is required
- referenced runs must be completed and match `business_id` + `site_id`

Response:
- `SEORecommendationRunRead`

## List recommendation runs
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs`

Response:
- `SEORecommendationRunListResponse`

## Get recommendation run
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}`

Response:
- `SEORecommendationRunRead`

## List recommendations for run
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/recommendations`

Response:
- `SEORecommendationListResponse`
- includes:
  - `items`
  - `total`
  - `by_category`
  - `by_severity`
  - `by_effort_bucket`

## Get recommendation by ID
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendations/{recommendation_id}`

Response:
- `SEORecommendationRead`

## Get deterministic recommendation report
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendation-runs/{recommendation_run_id}/report`

Response:
- `SEORecommendationRunReportRead`
- top-level shape:
  - `recommendation_run`
  - `rollups`
  - `recommendations`

`rollups` includes:
- `by_category`
- `by_severity`
- `by_effort_bucket`

## Status and Error Semantics
- `404` for business/site/run/recommendation not found in tenant scope
- `422` for deterministic lineage validation failures

## Deterministic Boundary
Phase 3A recommendation endpoints are deterministic.

They consume only persisted artifacts:
- `seo_audit_findings`
- `seo_competitor_comparison_findings`
- `seo_competitor_comparison_runs` rollups

They do not call AI providers.
