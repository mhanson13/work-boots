# SEO.ai Phase 2 API (Competitor Intelligence)

Status: Implemented on `main`  
Owner: Work Boots  
Scope: Current runtime API surface for Phase 2

---

## 1. Runtime Constraints

- FastAPI monolith.
- Business-scoped routes under `/api/businesses/{business_id}/seo/...`.
- Tenant scope resolved from `TenantContext` and validated with `resolve_tenant_business_id(...)`.
- Deterministic evidence first:
  - snapshot + comparison runs persist deterministic outputs.
  - AI is used only for manual-trigger comparison summaries.

---

## 2. Implemented Endpoints

## 2.1 Competitor sets

- `GET /api/businesses/{business_id}/seo/sites/{site_id}/competitor-sets`
- `POST /api/businesses/{business_id}/seo/sites/{site_id}/competitor-sets`
- `GET /api/businesses/{business_id}/seo/competitor-sets/{set_id}`
- `PATCH /api/businesses/{business_id}/seo/competitor-sets/{set_id}`

Create/update fields:
- `name` (required for create)
- `city` optional
- `state` optional
- `is_active`

## 2.2 Competitor domains

- `GET /api/businesses/{business_id}/seo/competitor-sets/{set_id}/domains`
- `POST /api/businesses/{business_id}/seo/competitor-sets/{set_id}/domains`
- `DELETE /api/businesses/{business_id}/seo/competitor-sets/{set_id}/domains/{domain_id}`

Create fields:
- `domain` or `base_url` (one required)
- `display_name` optional
- `notes` optional
- `is_active`

## 2.3 Snapshot runs

- `POST /api/businesses/{business_id}/seo/competitor-sets/{set_id}/snapshot-runs`
- `GET /api/businesses/{business_id}/seo/competitor-sets/{set_id}/snapshot-runs`
- `GET /api/businesses/{business_id}/seo/snapshot-runs/{run_id}`

Create fields:
- `client_audit_run_id` optional
- `max_domains`
- `max_pages_per_domain`
- `max_depth`
- `same_domain_only`

## 2.4 Deterministic comparison runs

- `POST /api/businesses/{business_id}/seo/competitor-sets/{set_id}/comparison-runs`
- `GET /api/businesses/{business_id}/seo/competitor-sets/{set_id}/comparison-runs`
- `GET /api/businesses/{business_id}/seo/comparison-runs/{run_id}`
- `GET /api/businesses/{business_id}/seo/comparison-runs/{run_id}/findings`
- `GET /api/businesses/{business_id}/seo/comparison-runs/{run_id}/report`

Create fields:
- `snapshot_run_id` (required)
- `baseline_audit_run_id` optional

Report shape:
- `run`
- `rollups`
- `findings`

## 2.5 Manual-trigger comparison summaries

- `POST /api/businesses/{business_id}/seo/comparison-runs/{run_id}/summarize`
- `GET /api/businesses/{business_id}/seo/comparison-runs/{run_id}/summaries`
- `GET /api/businesses/{business_id}/seo/comparison-runs/{run_id}/summaries/latest`
- `GET /api/businesses/{business_id}/seo/comparison-summaries/{summary_id}`

Summary generation rules:
- run must be completed.
- summary input is built from persisted comparison run + findings + rollups.
- summary failures persist as failed versions and do not mutate deterministic comparison outputs.

---

## 3. Response Contracts (Current)

## 3.1 `SEOCompetitorComparisonRunRead`

Includes:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `snapshot_run_id`, `baseline_audit_run_id`
- lifecycle: `status`, `started_at`, `completed_at`, `duration_ms`, `error_summary`
- rollup fields: `total_findings`, `critical_findings`, `warning_findings`, `info_findings`, `client_pages_analyzed`, `competitor_pages_analyzed`
- persisted count maps: `finding_type_counts_json`, `category_counts_json`, `severity_counts_json`
- metadata: `created_by_principal_id`, `created_at`, `updated_at`

## 3.2 `SEOCompetitorComparisonFindingListResponse`

Includes:
- `items`
- `total`
- `by_category`
- `by_severity`

Each finding includes:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `comparison_run_id`
- finding data: `finding_type`, `category`, `severity`, `title`, `details`, `rule_key`
- value deltas: `client_value`, `competitor_value`, `gap_direction`
- `evidence_json`
- `created_at`

## 3.3 `SEOCompetitorComparisonSummaryRead`

Includes:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `comparison_run_id`
- versioning: `version`
- lifecycle: `status` (`completed|failed`), `error_summary`
- content fields: `overall_gap_summary`, `top_gaps_json`, `plain_english_explanation`
- provider traceability: `provider_name`, `model_name`, `prompt_version`
- metadata: `created_by_principal_id`, `created_at`, `updated_at`

---

## 4. Status Codes

- `200` read success
- `201` create/run/summarize success
- `204` delete success for competitor domain removal
- `404` missing resource or cross-business access
- `422` validation/state violations

---

## 5. Security and Isolation

- business scope enforcement on every endpoint.
- repository/service lineage checks for set/site/run consistency.
- snapshot acquisition preserves crawler SSRF protections.
- summary endpoints never expose provider secrets or token material.

---

## 6. Out of Scope (Not Implemented in Phase 2 Runtime)

- automatic competitor discovery / SERP scraping
- rank tracking and backlink intelligence
- recommendation engine
- content generation and publishing
- background worker orchestration
