# SEO.ai Phase 2 Data Model

Status: Implemented on `main`  
Owner: Work Boots  
Scope: Runtime competitor-intelligence storage used by current Phase 2 APIs

---

## 1. Model Principles

- every Phase 2 table is business-scoped (`business_id`).
- lineage is explicit across site, set, run, finding, and summary records.
- deterministic comparison outputs are persisted separately from AI summaries.
- summary records are versioned per comparison run.

---

## 2. Implemented Tables

## 2.1 `seo_competitor_sets`

Purpose: group manual competitor domains for a site.

Core fields:
- `id`, `business_id`, `site_id`
- `name`, `city`, `state`, `is_active`
- `created_by_principal_id`
- `created_at`, `updated_at`

Constraints/indexes:
- unique: `(business_id, site_id, name)`
- indexes: `(business_id, site_id, is_active)`, `(business_id, created_at)`

## 2.2 `seo_competitor_domains`

Purpose: manual competitor domain targets within a set.

Core fields:
- `id`, `business_id`, `site_id`, `competitor_set_id`
- `domain`, `base_url`, `display_name`, `source`, `is_active`, `notes`
- `created_at`, `updated_at`

Constraints/indexes:
- unique: `(business_id, competitor_set_id, domain)`
- indexes: `(business_id, competitor_set_id, is_active)`, `(business_id, site_id)`

## 2.3 `seo_competitor_snapshot_runs`

Purpose: snapshot run lifecycle and diagnostics.

Core fields:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `client_audit_run_id`
- run config: `max_domains`, `max_pages_per_domain`, `max_depth`, `same_domain_only`
- lifecycle: `status`, `started_at`, `completed_at`, `duration_ms`, `error_summary`
- diagnostics: `domains_targeted`, `domains_completed`, `pages_attempted`, `pages_captured`, `pages_skipped`, `errors_encountered`
- metadata: `created_by_principal_id`, `created_at`, `updated_at`

Indexes:
- `(business_id, competitor_set_id, created_at)`
- `(business_id, status)`

## 2.4 `seo_competitor_snapshot_pages`

Purpose: persisted deterministic snapshot attributes per captured competitor page.

Core fields:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `snapshot_run_id`, `competitor_domain_id`
- page data: `url`, `status_code`, `title`, `meta_description`, `canonical_url`, `h1_json`, `h2_json`, `word_count`, `internal_link_count`
- fetch metadata: `fetched_at`, `error_summary`, `created_at`, `updated_at`

Constraints/indexes:
- unique: `(business_id, snapshot_run_id, competitor_domain_id, url)`
- indexes: `(business_id, snapshot_run_id)`, `(business_id, competitor_domain_id)`

## 2.5 `seo_competitor_comparison_runs`

Purpose: deterministic comparison run lifecycle and persisted rollups.

Core fields:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `snapshot_run_id`, `baseline_audit_run_id`
- lifecycle: `status`, `started_at`, `completed_at`, `duration_ms`, `error_summary`
- aggregate counts: `total_findings`, `critical_findings`, `warning_findings`, `info_findings`, `client_pages_analyzed`, `competitor_pages_analyzed`
- persisted rollups: `metric_rollups_json`, `finding_type_counts_json`, `category_counts_json`, `severity_counts_json`
- metadata: `created_by_principal_id`, `created_at`, `updated_at`

Indexes:
- `(business_id, competitor_set_id, created_at)`
- `(business_id, snapshot_run_id)`
- `(business_id, status)`

## 2.6 `seo_competitor_comparison_findings`

Purpose: deterministic comparison findings.

Core fields:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `comparison_run_id`
- finding attributes: `finding_type`, `category`, `severity`, `title`, `details`, `rule_key`
- value comparison: `client_value`, `competitor_value`, `gap_direction`, `evidence_json`
- timestamps: `created_at`, `updated_at`

Indexes:
- `(business_id, comparison_run_id, created_at)`
- `(business_id, category)`
- `(business_id, severity)`
- `(business_id, finding_type)`

## 2.7 `seo_competitor_comparison_summaries`

Purpose: versioned AI comparison summaries for completed comparison runs.

Core fields:
- lineage: `id`, `business_id`, `site_id`, `competitor_set_id`, `comparison_run_id`
- versioning/lifecycle: `version`, `status`, `error_summary`
- summary content: `overall_gap_summary`, `top_gaps_json`, `plain_english_explanation`
- provider traceability: `provider_name`, `model_name`, `prompt_version`
- metadata: `created_by_principal_id`, `created_at`, `updated_at`

Constraints/indexes:
- unique: `(business_id, comparison_run_id, version)`
- indexes: `(business_id, comparison_run_id, created_at)`, `(business_id, status)`

---

## 3. Lineage Relationships

- `seo_sites` -> many `seo_competitor_sets`
- `seo_competitor_sets` -> many `seo_competitor_domains`
- `seo_competitor_sets` -> many `seo_competitor_snapshot_runs`
- `seo_competitor_snapshot_runs` -> many `seo_competitor_snapshot_pages`
- `seo_competitor_snapshot_runs` -> many `seo_competitor_comparison_runs`
- `seo_competitor_comparison_runs` -> many `seo_competitor_comparison_findings`
- `seo_competitor_comparison_runs` -> many `seo_competitor_comparison_summaries`

Service/repository lineage guards enforce:
- business and site consistency across parent/child relationships
- no cross-business references for snapshot/comparison/summary operations

---

## 4. Persisted Rollups and Versioning

- comparison run rollups are persisted on `seo_competitor_comparison_runs` (`*_counts_json`, `metric_rollups_json`).
- comparison summaries are stored as separate versioned records; repeated manual generation increments `version`.
- failed summary attempts persist a failed version and do not mutate deterministic comparison run/findings data.

---

## 5. Out of Scope

- SERP/rank/backlink schemas
- recommendation/content-generation schemas
- queue/orchestration tables
