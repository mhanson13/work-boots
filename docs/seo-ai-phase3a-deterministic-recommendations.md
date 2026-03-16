# SEO.ai Phase 3A: Deterministic Recommendations

## Overview
Phase 3A adds deterministic recommendation generation on top of persisted SEO evidence.

Recommendations are generated from:
- persisted first-party audit findings (`seo_audit_findings`)
- persisted competitor comparison findings and rollups (`seo_competitor_comparison_findings`, `seo_competitor_comparison_runs`)

AI is not used in this phase.

## Scope
Implemented in Phase 3A:
- persisted recommendation runs
- persisted recommendation records
- deterministic recommendation engine using explicit rule templates
- business-scoped API endpoints to create/list/read recommendation runs and recommendations
- deterministic recommendation run report contract

Out of scope in Phase 3A:
- workflow orchestration (assignment, status boards, automation)
- AI recommendation narratives
- recommendation publishing/activation pipelines

## Deterministic Inputs
Recommendation runs accept:
- `audit_run_id`
- `comparison_run_id`
- or both

Validation rules:
- at least one lineage input is required
- referenced runs must belong to the same business and site
- referenced runs must be `completed`

## Deterministic Recommendation Rules
The engine maps persisted finding patterns to fixed templates:
- audit finding types -> technical/SEO/content/structure remediation recommendations
- competitor comparison gaps (`*_gap`, `client_trails`) -> competitor gap closure recommendations

Priority is deterministic from:
- severity
- grouped finding counts
- source type (audit/comparison)

Duplicate recommendations are merged by deterministic `rule_key`.

## Persistence and Traceability
Each run persists:
- lineage (`audit_run_id`, `comparison_run_id`)
- status lifecycle (`queued`, `running`, `completed`, `failed`)
- aggregate counts (total, severity, category, effort bucket)
- timing/error metadata

Each recommendation persists:
- deterministic `rule_key`
- category/severity
- deterministic `priority_score`
- deterministic `effort_bucket`
- evidence summary payload

## Tenant Isolation
All records are business-scoped (`business_id`) and site-scoped (`site_id`):
- route-level business context checks
- service-level lineage validation
- repository-level scope guards
- DB constraints/indexes for business/site access paths

## Notes for Next Phases
Deferred intentionally:
- Phase 3B: workflow/prioritization operations beyond deterministic fields
- Phase 3C: AI recommendation narratives
- Phase 4: automation/operational execution flows
