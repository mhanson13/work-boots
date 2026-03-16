# SEO.ai Phase 2A Foundations Summary

## What Was Added
- Business-scoped competitor foundation models and migration:
  - `seo_competitor_sets`
  - `seo_competitor_domains`
  - `seo_competitor_snapshot_runs`
  - `seo_competitor_snapshot_pages`
- Key integrity constraints and indexes:
  - unique competitor set name per business/site
  - unique competitor domain per business/set
  - unique snapshot page URL per business/run/domain
  - indexes for business/site/set/run lookups and status timelines
- New repository/service layer for competitor set, member, and snapshot-run lifecycle:
  - business ownership checks
  - site/set/domain lineage validation
  - cross-business reference rejection
- New business-scoped SEO endpoints:
  - create/list/get/patch competitor sets
  - add/list/remove competitor domains
  - create/list/get competitor snapshot runs (lineage trigger records)

## What Was Intentionally Deferred
- Deterministic competitor comparison engine
- Competitor scoring/ranking logic
- AI competitor gap summaries
- Background worker orchestration for snapshot execution
- Expanded crawling behavior beyond current bounded/safe controls

## Next Safe Milestone
Implement Phase 2B deterministic comparison execution:
- consume persisted snapshot outputs
- compute deterministic gap findings
- persist comparison runs + findings
- expose business-scoped comparison read APIs
- keep AI out of comparison generation and reserve AI for later summary-only endpoints
