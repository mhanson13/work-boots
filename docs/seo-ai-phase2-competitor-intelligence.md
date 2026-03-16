# SEO.ai Phase 2: Competitor Intelligence

Status: Implemented on `main`  
Owner: Work Boots  
Depends on: Phase 1 + Phase 1.5  
Scope: manual competitor management, snapshot runs, deterministic comparison runs, manual-trigger comparison summaries

---

## 1. Overview

Phase 2 extends SEO.ai beyond first-party audit runs by adding business-scoped competitor intelligence.

Implemented capabilities:
- business-scoped competitor sets and domains
- competitor snapshot runs and persisted snapshot pages
- deterministic comparison runs, findings, and run-level rollups
- manual-trigger AI comparison summaries grounded in persisted deterministic outputs

---

## 2. Implemented Scope

### In scope
- competitor set and domain registration
- snapshot run lifecycle (`queued|running|completed|failed`)
- deterministic comparison run lifecycle (`queued|running|completed|failed`)
- persisted comparison findings and rollup/count JSON
- manual-trigger comparison summaries with versioning and provider metadata

### Explicitly out of scope
- automatic competitor discovery / SERP scraping
- ranking/backlink features
- recommendation engines
- AI-generated findings
- AI-generated content or publishing
- queue/worker architecture changes

---

## 3. Runtime Workflow

## 3.1 Competitor setup
1. Create a competitor set for a site.
2. Add one or more competitor domains to the set.

## 3.2 Snapshot run
1. Trigger snapshot run for competitor set.
2. Persist run diagnostics and captured competitor pages.

## 3.3 Deterministic comparison run
1. Trigger comparison run from a completed snapshot run.
2. Optionally bind to a baseline first-party audit run.
3. Persist comparison findings and run rollups.

## 3.4 Comparison summary
1. Manually trigger summary for completed comparison run.
2. Build provider input from persisted run + findings + rollups.
3. Persist versioned summary (`completed` or `failed`).

---

## 4. Deterministic Comparison Dimensions (Current)

Current deterministic metrics are count/coverage deltas built from persisted data:
- page count
- missing title count
- missing meta description count
- missing H1 count
- thin content count
- missing canonical count
- missing internal links count
- title coverage percent
- meta description coverage percent
- H1 coverage percent
- canonical coverage percent
- internal link coverage percent

Current deterministic finding behavior also includes:
- `missing_client_baseline` when no completed first-party baseline is available
- `empty_competitor_snapshot` when the snapshot run has no captured competitor pages

Comparison outputs persist:
- severity/category/type counts
- metric rollups with client/competitor values and delta
- findings with evidence payloads

---

## 5. Comparison Summaries (Current)

Comparison summaries are separate persisted resources tied to a comparison run:
- versioned per `(business_id, comparison_run_id)`
- statuses: `completed`, `failed`
- include provider/model/prompt metadata for traceability
- include `overall_gap_summary`, `top_gaps_json`, and `plain_english_explanation`

Failure isolation:
- failed summary attempts persist a failed version with `error_summary`
- deterministic comparison run/findings/rollups remain unchanged

---

## 6. Architecture and Isolation

- FastAPI monolith with service/repository layering.
- Route handlers stay thin; deterministic logic lives in services.
- Tenant context is enforced at route/service/repository boundaries.
- Parent-child lineage checks validate site/set/run relationships.
- Cross-business access returns not found behavior.
- Snapshot capture path reuses crawler security controls (including SSRF protections).

---

## 7. Future Work (Not Implemented in Phase 2)

Potential later phases may add:
- automated competitor discovery
- recommendation synthesis
- richer strategy outputs
- automation/queue execution models

These are intentionally not part of current Phase 2 runtime behavior.
