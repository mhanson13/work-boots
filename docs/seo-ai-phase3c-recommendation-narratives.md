# SEO.ai Phase 3C: AI Recommendation Narratives

## Overview
Phase 3C adds AI narrative generation for deterministic recommendation runs.

Narratives explain persisted recommendation evidence, workflow state, and prioritization context. Recommendation generation remains deterministic and unchanged.

## Scope Implemented
- versioned, persisted recommendation narrative records
- manual-trigger narrative generation per recommendation run
- list/latest/by-id narrative retrieval
- provider/model/prompt traceability fields
- failure-isolated narrative versioning (`failed` versions are persisted)
- business-scoped and site-scoped API access controls
- real provider integration (OpenAI) with structured-output validation
- governed prompt construction from persisted deterministic artifacts only
- local/test mock fallback path without introducing a second narrative subsystem

## Grounding Boundary
Narrative generation consumes persisted artifacts only:
- `seo_recommendation_runs`
- `seo_recommendations`
- persisted workflow/prioritization fields on recommendations

Narrative generation does not:
- generate or modify recommendations
- create findings
- change deterministic scores, severity, effort, or workflow state
- read live crawler/page payloads as source of truth
- auto-apply settings or execute actions

## Failure Isolation
Provider failures create a new narrative version with:
- `status=failed`
- populated `error_message`
- persisted provider/model/prompt metadata for diagnostics

Recommendation runs and recommendation records are not mutated during narrative failure handling.

## Provider and Prompt Governance
- provider selection follows existing AI runtime config (`AI_PROVIDER_NAME`, `AI_MODEL_NAME`, `AI_TIMEOUT_VALUE`)
- OpenAI credentials use `AI_PROVIDER_API_KEY`
- prompt includes deterministic recommendation rollups and bounded recommendation previews
- prompt treats all context fields as data (not instructions)
- structured response schema requires:
  - `narrative_text`
  - `top_themes`
  - `sections`

`sections.recommendation_references` is filtered to known persisted recommendation IDs before persistence.

## Out of Scope in Phase 3C
- AI-generated recommendation items
- AI prioritization decisions
- automation/schedulers/queues
- remediation execution

Future work remains:
- Phase 4 automation and operationalization
