# SEO.ai Phase 2B Deterministic Comparison Foundations Summary

## What Was Added
- Persisted deterministic comparison data model:
  - `seo_competitor_comparison_runs`
  - `seo_competitor_comparison_findings`
- Added migration `0016_seo_competitor_comparison_foundations` with business-scoped foreign keys and query indexes.
- Added a dedicated deterministic comparison service:
  - consumes persisted first-party audit data and persisted competitor snapshot pages only
  - produces deterministic, evidence-backed findings only
  - no AI use and no recommendation/content generation
- Added business-scoped comparison APIs:
  - create comparison run
  - list comparison runs for a competitor set
  - get comparison run details
  - list comparison findings with category/severity aggregates
  - get comparison report payload (run + findings)
- Added lineage and tenant-safety validation:
  - snapshot run must belong to business/site/set and be completed
  - baseline audit run (if provided/resolved) must match business/site and be completed
  - cross-business lookups return not found/validation failures

## Deterministic Comparison Coverage (Phase 2B)
- Page coverage gap (`page_count_gap`)
- Missing title count gap
- Missing meta description count gap
- Missing H1 count gap
- Thin content count gap
- Missing canonical count gap
- Missing baseline / empty snapshot sentinel findings for partial-data stability

## What Was Deferred
- AI competitor summaries
- Recommendation engine and strategy generation
- Weighted ranking/scoring heuristics beyond simple deterministic deltas
- Snapshot execution redesign or background worker orchestration
- Any crawler scope expansion

## Next Safe Milestone
Phase 2C: deterministic comparison enrichment and read-model hardening:
- expand deterministic comparison dimensions using already persisted snapshot/audit fields
- add comparison run-level rollups and trend-ready report fields
- keep AI out of comparison generation and reserve AI for a later summary-only phase
