# SEO.ai Phase 3B API

## Architecture Contract
- business-scoped routes
- deterministic recommendation records only
- no AI recommendation generation
- thin routes + service-layer workflow validation

Primary route prefixes:
- `/api/businesses/{business_id}/seo/...`
- `/api/v1/businesses/{business_id}/seo/...` (site-scoped compatibility)

## Endpoints

## List site recommendations
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendations`

Supported query filters/sort:
- `status`
- `category`
- `severity`
- `effort_bucket`
- `priority_band`
- `assigned_principal_id`
- `source_type` (`audit`, `comparison`, `mixed`)
- `recommendation_run_id`
- `sort_by` (`priority_score`, `priority_band`, `severity`, `created_at`, `updated_at`, `due_at`)
- `sort_order` (`asc`, `desc`)

Response:
- `SEORecommendationListResponse`

## Get recommendation
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendations/{recommendation_id}`

Response:
- `SEORecommendationRead`

## Update recommendation workflow
`PATCH /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendations/{recommendation_id}`

Request:
- `SEORecommendationWorkflowUpdateRequest`
- partial updates allowed

Supported fields:
- `status`
- `decision`
- `decision_reason`
- `assigned_principal_id`
- `due_at`
- `snoozed_until`

Response:
- `SEORecommendationRead`

## Deterministic backlog
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendations/backlog`

Response:
- `SEORecommendationBacklogRead`

## Deterministic prioritized report
`GET /api/v1/businesses/{business_id}/seo/sites/{site_id}/recommendations/prioritized-report`

Response:
- `SEORecommendationPrioritizedReportRead`

Top-level report shape:
- scope metadata (`business_id`, `site_id`, `generated_at`)
- total recommendation count
- backlog count
- aggregate rollups:
  - `by_status`
  - `by_category`
  - `by_severity`
  - `by_effort_bucket`
  - `by_priority_band`
- `backlog` list contract (`SEORecommendationListResponse`)

## Status and Error Semantics
- `404` for out-of-scope or missing business/site/recommendation resources
- `422` for invalid workflow updates (transition violations, invalid assignee, invalid snooze fields)

## Deterministic Boundary
Phase 3B workflow/prioritization APIs operate only on persisted recommendation state.

They do not call AI providers and do not create new recommendation generation logic.
