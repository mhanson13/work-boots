# SEO.ai Phase 3B Data Model

## Schema Changes
Phase 3B extends `seo_recommendations` with workflow and prioritization fields.

No new Phase 3B tables were introduced.

## `seo_recommendations` Additions
- `priority_band` (`low` | `medium` | `high` | `critical`)
- `status` (`open` | `in_progress` | `accepted` | `dismissed` | `snoozed` | `resolved`)
- `decision` (`accept` | `dismiss` | `snooze` | `resolve` | `reopen` | `start`) nullable
- `decision_reason` nullable text
- `assigned_principal_id` nullable
- `due_at` nullable timestamp
- `snoozed_until` nullable timestamp
- `resolved_at` nullable timestamp
- `updated_by_principal_id` nullable

## Integrity Constraints
- `ck_seo_recommendations_status`
- `ck_seo_recommendations_decision`
- `ck_seo_recommendations_priority_band`
- composite FK:
  - `fk_seo_recommendations_business_assigned_principal`
  - (`business_id`, `assigned_principal_id`) -> `principals (business_id, id)`

## Index Additions
Added for workflow list/backlog/report access patterns:
- `ix_seo_recommendations_business_site_status_priority`
- `ix_seo_recommendations_business_priority_band`
- `ix_seo_recommendations_business_assigned_principal`
- `ix_seo_recommendations_business_due_at`
- `ix_seo_recommendations_business_snoozed_until`

## Migration
Alembic revision: `0020_seo_recommendation_workflow_fields`

Migration behavior:
- adds new workflow/prioritization columns
- backfills `priority_band` from existing `priority_score`
- adds new constraints, FK, and indexes
