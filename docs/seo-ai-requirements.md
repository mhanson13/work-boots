# SEO.ai Requirements

Status: Draft  
Owner: mbsrn  
Scope: Contractor SEO audit, competitor analysis, content recommendation, and AI-assisted content generation  
Target repo: mbsrn

---

## 1. Purpose

SEO.ai is a new business-scoped capability inside mbsrn that helps contractor businesses improve local search visibility through a combination of deterministic website analysis, competitor gap detection, AI-assisted recommendations, and AI-generated draft content.

SEO.ai extends the existing mbsrn product rather than living as a separate system. mbsrn already supports business-scoped operations, persisted principals, credential lifecycle, and project documentation under `docs/`, which makes it a suitable foundation for this module. The current repo is a monolithic FastAPI service for operator-facing SEO operations and follow-up workflows, so SEO.ai should fit that architecture and documentation pattern.

---

## 2. Product Goals

### 2.1 Primary goals
- Allow a business user to register a website for SEO analysis
- Crawl and analyze that website for basic on-page SEO health
- Identify missing, weak, duplicate, or under-optimized pages and sections
- Compare a client site against competitors in the same market
- Recommend a better site structure for local contractor SEO
- Generate AI-assisted draft content and metadata
- Produce client-ready reports and prioritized action plans
- Support repeat scans over time for monitoring and trend analysis

### 2.2 Secondary goals
- Build a reusable workflow that can scale across many contractor clients
- Reduce manual SEO agency effort through automation
- Keep AI outputs reviewable, versioned, and auditable
- Fit cleanly into the existing mbsrn auth, business scoping, and API patterns

### 2.3 Non-goals for MVP
- Full publishing to external CMS platforms
- Full backlink analysis
- Full rank tracking across all search terms
- Paid search management
- Social media management
- Autonomous publishing without human review

---

## 3. Guiding Principles

### 3.1 Deterministic first
Use deterministic extraction and scoring for factual data:
- crawl results
- metadata presence
- heading structure
- internal links
- word count
- canonical detection
- image alt detection

Use AI for:
- summarization
- prioritization
- recommendation wording
- page brief generation
- content drafting
- plain-English explanations

### 3.2 Human in the loop
All AI-generated outputs are drafts unless explicitly approved by a user.

### 3.3 Business-scoped by default
All SEO.ai records must belong to a `business_id`.

### 3.4 Auditable
All runs, generation events, approvals, and major state changes must be traceable.

### 3.5 Modular rollout
The module should be deliverable in phases so implementation can proceed incrementally.

---

## 4. Primary Users

### 4.1 Internal agency/operator user
A mbsrn operator or admin running SEO workflows on behalf of a contractor client.

### 4.2 Contractor business owner
A business user reviewing findings, reports, and generated recommendations.

### 4.3 Future admin/reviewer
A user responsible for approving generated content before use.

---

## 5. Core Domain Concepts

The following logical entities should exist, whether implemented immediately or phased in later:

- `seo_sites`
- `seo_audit_runs`
- `seo_audit_pages`
- `seo_audit_findings`
- `seo_competitor_sets`
- `seo_competitor_domains`
- `seo_competitor_snapshots`
- `seo_page_recommendations`
- `seo_content_briefs`
- `seo_generated_assets`
- `seo_reports`
- `seo_scan_schedules`
- `seo_generation_events`

These names may be adjusted to match project naming conventions, but the concepts should remain.

---

## 6. Functional Requirements

### 6.1 Site Registration

#### Description
A business must be able to register one or more websites or domains for SEO analysis.

#### Requirements
- The system must allow creation of a website record tied to `business_id`
- A site record must include at minimum:
  - `business_id`
  - `base_url`
  - `display_name`
  - `industry` or `business_category`
  - `primary_location`
  - `service_areas` optional
  - `is_active`
- The system must normalize the base URL for consistent storage
- The system must validate that a site URL is syntactically valid
- The system must support one business having multiple tracked sites in the future
- The system should support marking one site as primary

#### Acceptance criteria
- A valid site can be created, retrieved, updated, and listed by business
- Invalid URLs are rejected with validation errors
- A site cannot be accessed across business boundaries

### 6.2 Site Audit Engine

#### Description
The platform must crawl a client website and extract core on-page SEO information.

#### Inputs
- `business_id`
- `site_id`
- optional crawl settings:
  - `max_pages`
  - `max_depth`
  - `same_domain_only`
  - `include_paths`
  - `exclude_paths`

#### Deterministic requirements
The audit engine must:
- fetch the base page
- discover internal links within allowed scope
- crawl up to configured limits
- store discovered pages
- extract from each page where available:
  - final URL
  - HTTP status
  - title tag
  - meta description
  - H1 headings
  - H2 headings
  - canonical tag
  - robots meta if present
  - word count
  - internal outgoing links
  - image count
  - missing alt count if feasible
  - detected phone/email/address fragments if feasible
  - last fetched timestamp

#### Audit finding rules
The engine must detect at minimum:
- missing title
- duplicate title
- title too short
- title too long
- missing meta description
- duplicate meta description
- meta description too short
- meta description too long
- missing H1
- multiple H1s
- low word count / thin content
- orphaned or weakly linked pages if derivable
- missing canonical
- broken internal links if derivable
- missing location references
- missing service references
- weak trust/conversion signals based on rule heuristics
- absence of key page types based on recommended contractor pattern

#### Output requirements
An audit run must produce:
- run status
- crawl summary
- page inventory
- finding inventory
- severity counts
- category counts

#### Acceptance criteria
- A user can create an audit run for a site
- The run transitions through states such as `queued`, `running`, `completed`, `failed`
- Findings are stored and retrievable by run
- Findings are business-scoped and site-scoped
- Failed runs persist a reason or error summary

### 6.3 AI Audit Summary

#### Description
AI should summarize raw audit findings into human-readable language.

#### Requirements
- The system must generate an executive summary for a completed audit run
- The summary must explain:
  - overall site health
  - top issues
  - highest-priority fixes
  - likely SEO impact
- The summary must be based on stored findings, not page hallucination
- The summary must be stored separately from deterministic findings
- The system must record prompt version and model metadata for traceability

#### Acceptance criteria
- A completed audit can generate a concise summary
- Summary generation failure does not invalidate the deterministic audit run
- A regenerated summary creates a new version or updates with audit history preserved

### 6.4 Competitor Analysis Engine

#### Description
The platform must compare a client site against relevant competitors.

#### Inputs
- `business_id`
- `site_id`
- target market info:
  - `city`
  - `state`
  - optional manual competitor domains
  - optional service keywords

#### Functional requirements
The system must support:
- manual competitor entry
- automated competitor discovery later or in a phased implementation
- storing competitor domains per business/site context
- taking snapshots of competitor homepages and selected internal pages
- extracting comparable SEO features where feasible

#### Comparison dimensions
The system should compare:
- number of service pages
- existence of core trust pages
- presence of process page
- presence of FAQ page
- local market mentions
- page/topic coverage
- metadata patterns
- heading/topic patterns
- depth of visible content

#### AI-assisted requirements
AI should:
- summarize why competitors appear stronger or weaker
- identify common patterns among top competitors
- identify missing page types or topic areas on the client site
- propose opportunity areas

#### Acceptance criteria
- A competitor set can be created for a site
- Competitor domains can be stored and listed
- A comparison summary can be generated from stored snapshots/findings
- Competitor analysis remains linked to the originating business and site

### 6.5 Site Architecture Recommendation Engine

#### Description
The platform must recommend a better sitemap/page hierarchy for contractor SEO.

#### Requirements
Given:
- business category
- services offered
- service area or city
- audit findings
- competitor patterns where available

The system must generate recommended page types such as:
- Home
- About
- Contact
- Services overview
- individual service pages
- Process page
- FAQ page
- Reviews/testimonials page
- Portfolio/project gallery page
- service-area or city pages where appropriate

Each recommendation should include:
- page type
- suggested slug
- purpose
- target intent
- whether page is missing, weak, or already present
- implementation priority

#### AI-assisted requirements
AI should generate:
- rationale for each recommended page
- suggested H1
- outline or heading structure
- CTA suggestions
- internal linking suggestions

#### Acceptance criteria
- A recommendation set can be generated from site and business inputs
- Each recommended page is stored as a discrete record
- Recommendations are versioned or tied to the run that produced them

### 6.6 Content Brief Generation

#### Description
The platform must produce structured briefs before full content drafting.

#### Requirements
For a recommended page, the system must be able to generate a brief containing:
- page purpose
- target audience
- target service or topic
- target location or region
- suggested angle/value proposition
- suggested H1
- suggested H2 sections
- key points to include
- suggested CTA
- related internal links
- notes for human review

#### Acceptance criteria
- A brief can be generated from a page recommendation
- The brief is editable by a user
- The brief can be used as input for content generation

### 6.7 AI Content Generation Engine

#### Description
The system must generate draft content assets from structured inputs.

#### Supported asset types
- service page draft
- homepage copy variants
- process page draft
- FAQ draft
- about/trust copy
- title tag suggestions
- meta description suggestions
- GBP business description
- GBP Q&A suggestions
- short CTA variants

#### Requirements
The system must:
- accept a structured brief
- support configurable tone and brand style
- support location-aware content
- generate one or more variants
- store outputs with version history
- mark outputs as draft by default
- allow regeneration without deleting previous versions

#### Content safety and quality requirements
The system must:
- avoid unsupported factual claims where possible
- flag unverifiable claims for human review
- avoid spammy keyword stuffing
- avoid duplicate asset generation where practical
- preserve prompt metadata and model/version metadata

#### Acceptance criteria
- A content brief can generate one or more draft assets
- Draft assets can be listed and retrieved
- A user can mark a draft as approved, rejected, or superseded
- Regenerated assets do not overwrite history silently

### 6.8 Metadata Generation

#### Description
The system must generate optimized metadata suggestions for existing or recommended pages.

#### Requirements
For each page, the system should be able to generate:
- suggested title tag
- suggested meta description
- optionally OG title/description later

The system must also evaluate:
- title length
- description length
- duplication risk
- missing location or service intent

#### Acceptance criteria
- Metadata suggestions can be generated for a page
- Suggestions are stored as draft assets or a related metadata record
- Metadata suggestions are reviewable and versioned

### 6.9 Reporting Engine

#### Description
The platform must generate human-readable reports from structured SEO.ai data.

#### Report types
- initial audit report
- competitor gap report
- content roadmap
- recommended architecture report
- monitoring report
- monthly summary report

#### Requirements
Reports should include:
- executive summary
- top priorities
- issue counts by severity
- notable page findings
- competitor insights where applicable
- recommended next steps
- generated assets summary where applicable

The system should initially support:
- structured JSON response
- markdown-renderable output

PDF export can be deferred.

#### Acceptance criteria
- A report can be generated for a completed run or recommendation set
- Report generation does not mutate source records
- Reports are business-scoped and versioned

### 6.10 Monitoring and Re-Scan Engine

#### Description
The system must support recurring site scans and change detection.

#### Requirements
- A site can have a scan schedule
- A scheduled run must create a new audit run
- The system must compare new results against the prior completed run
- The system must identify:
  - newly introduced issues
  - resolved issues
  - page count changes
  - metadata improvements or regressions
- The system should generate a change summary

#### Acceptance criteria
- A site can have recurring scan settings stored
- A new run can be triggered from a schedule or manually
- Comparison results are accessible and linked to both runs

---

## 7. Workflow Requirements

### 7.1 Initial onboarding workflow
1. Create site record for business
2. Run baseline audit
3. Generate audit summary
4. Add competitors or generate competitor set
5. Generate competitor gap summary
6. Generate site architecture recommendations
7. Generate content briefs for top-priority pages
8. Generate draft content assets
9. Generate client-facing report

### 7.2 Ongoing optimization workflow
1. Re-run audit
2. Compare against previous run
3. Regenerate summary
4. Identify next priorities
5. Generate refreshed metadata/content where needed
6. Produce progress report

---

## 8. API Requirements

The exact route design may evolve, but the MVP should support endpoints in the style already used by mbsrn business-scoped APIs. The current repo already uses business-scoped endpoints for principal and credential management, so SEO.ai should follow the same approach.

### Suggested endpoint families

#### Sites
- `GET /api/businesses/{business_id}/seo/sites`
- `POST /api/businesses/{business_id}/seo/sites`
- `GET /api/businesses/{business_id}/seo/sites/{site_id}`
- `PATCH /api/businesses/{business_id}/seo/sites/{site_id}`

#### Audit runs
- `POST /api/businesses/{business_id}/seo/sites/{site_id}/audit-runs`
- `GET /api/businesses/{business_id}/seo/sites/{site_id}/audit-runs`
- `GET /api/businesses/{business_id}/seo/audit-runs/{run_id}`
- `GET /api/businesses/{business_id}/seo/audit-runs/{run_id}/findings`
- `POST /api/businesses/{business_id}/seo/audit-runs/{run_id}/summarize`

#### Competitors
- `GET /api/businesses/{business_id}/seo/sites/{site_id}/competitors`
- `POST /api/businesses/{business_id}/seo/sites/{site_id}/competitors`
- `POST /api/businesses/{business_id}/seo/sites/{site_id}/competitor-analysis`

#### Recommendations
- `POST /api/businesses/{business_id}/seo/sites/{site_id}/recommendations`
- `GET /api/businesses/{business_id}/seo/sites/{site_id}/recommendations`

#### Briefs and generated assets
- `POST /api/businesses/{business_id}/seo/recommendations/{recommendation_id}/brief`
- `POST /api/businesses/{business_id}/seo/briefs/{brief_id}/generate`
- `GET /api/businesses/{business_id}/seo/generated-assets/{asset_id}`
- `PATCH /api/businesses/{business_id}/seo/generated-assets/{asset_id}`

#### Reports
- `POST /api/businesses/{business_id}/seo/reports`
- `GET /api/businesses/{business_id}/seo/reports/{report_id}`

#### Schedules
- `GET /api/businesses/{business_id}/seo/sites/{site_id}/schedule`
- `PUT /api/businesses/{business_id}/seo/sites/{site_id}/schedule`

---

## 9. Data Model Requirements

This section describes the minimum conceptual fields expected.

### 9.1 `seo_sites`
- `id`
- `business_id`
- `display_name`
- `base_url`
- `normalized_domain`
- `industry`
- `primary_location`
- `service_areas_json` or equivalent
- `is_active`
- `created_at`
- `updated_at`

### 9.2 `seo_audit_runs`
- `id`
- `business_id`
- `site_id`
- `status`
- `started_at`
- `completed_at`
- `max_pages`
- `max_depth`
- `pages_discovered`
- `pages_crawled`
- `error_summary`
- `created_by_principal_id` nullable
- `created_at`

### 9.3 `seo_audit_pages`
- `id`
- `audit_run_id`
- `business_id`
- `site_id`
- `url`
- `status_code`
- `title`
- `meta_description`
- `canonical_url`
- `h1_json`
- `h2_json`
- `word_count`
- `internal_link_count`
- `image_count`
- `missing_alt_count`
- `fetched_at`

### 9.4 `seo_audit_findings`
- `id`
- `audit_run_id`
- `business_id`
- `site_id`
- `page_id` nullable
- `finding_type`
- `category`
- `severity`
- `title`
- `details`
- `rule_key`
- `suggested_fix`
- `created_at`

### 9.5 `seo_competitor_domains`
- `id`
- `business_id`
- `site_id`
- `domain`
- `display_name`
- `source`
- `is_active`
- `created_at`

### 9.6 `seo_page_recommendations`
- `id`
- `business_id`
- `site_id`
- `source_audit_run_id` nullable
- `page_type`
- `slug`
- `title`
- `status`
- `priority`
- `rationale`
- `outline_json`
- `created_at`

### 9.7 `seo_content_briefs`
- `id`
- `business_id`
- `site_id`
- `recommendation_id`
- `brief_json`
- `status`
- `created_by_principal_id`
- `created_at`
- `updated_at`

### 9.8 `seo_generated_assets`
- `id`
- `business_id`
- `site_id`
- `brief_id` nullable
- `asset_type`
- `title`
- `content`
- `status`
- `version`
- `model_name`
- `prompt_version`
- `created_by_principal_id`
- `approved_by_principal_id` nullable
- `created_at`
- `updated_at`

### 9.9 `seo_reports`
- `id`
- `business_id`
- `site_id`
- `report_type`
- `source_run_id` nullable
- `content_markdown`
- `content_json`
- `status`
- `created_at`

---

## 10. Permissions and Business Scoping

### Requirements
- SEO.ai data must be isolated by `business_id`
- Access must follow the same business-scoped principles as existing mbsrn modules
- Admin-only actions may be required later for destructive operations
- All reads and writes must verify the actor can access the target business
- Cross-business access must be rejected

### Acceptance criteria
- No SEO.ai record can be retrieved from a different business context
- Audit runs and generated assets are filtered by business consistently

---

## 11. Audit and Traceability Requirements

The existing repo already emphasizes audit visibility for sensitive flows, and SEO.ai should follow the same spirit for AI and content-generation operations.

### Requirements
The system must capture:
- who initiated an audit run, if authenticated
- when a run started and completed
- model and prompt version for AI generation
- asset approval or rejection actions
- regeneration history
- report generation events

This can be implemented with dedicated SEO event tables first, and later integrated into a broader audit framework.

---

## 12. Background Processing Requirements

### Requirements
The system should be designed assuming some SEO workloads are asynchronous:
- crawling
- competitor snapshotting
- AI summarization
- report generation

The implementation may begin with synchronous execution for local MVP use, but code structure should anticipate background job execution later.

### Acceptance criteria
- Service boundaries are written so long-running tasks can move behind a queue later
- Status fields exist for long-running operations

---

## 13. Error Handling Requirements

### Requirements
- Invalid URL inputs must return validation errors
- Unreachable pages must not crash the full audit run
- Partial crawl failures must still preserve usable findings where possible
- AI failures must not delete deterministic audit data
- Clear run status and error summaries must be exposed

### Acceptance criteria
- A failed AI summary still leaves a completed crawl
- A failed crawl persists failure state and reason
- API consumers can distinguish validation errors from runtime failures

---

## 14. Non-Functional Requirements

### 14.1 Maintainability
- The implementation must fit the current monolith structure
- New services, schemas, repositories, and routes should follow existing project conventions
- Feature growth should not require immediate microservice decomposition

### 14.2 Testability
- Rule-based finding detection must be unit testable
- Content generation boundaries must be mockable
- API endpoints must have integration tests
- Business-scoping behavior must have explicit tests

### 14.3 Performance
- MVP should handle small contractor sites reliably
- Crawl limits must be configurable to prevent runaway scans
- Pages should be processed within reasonable limits for local development

### 14.4 Security
- Respect existing API auth model and business scoping
- Avoid storing secrets in SEO.ai records
- Sanitize fetched content as needed before downstream use
- Prevent SSRF-style abuse through URL restrictions and validation

### 14.5 Observability
- Log audit run lifecycle
- Log high-level page crawl outcomes
- Log generation failures with enough detail for debugging
- Avoid logging full sensitive prompt payloads if they may contain customer-specific content

---

## 15. MVP Delivery Phases

### Phase 1: Baseline audit
Scope:
- site registration
- audit run creation
- crawl basic pages
- extract metadata/headings/word count/internal links
- create audit findings
- list findings by run
- AI executive summary

Exit criteria:
- a business can register a site and receive a stored audit with summary

Implementation checklist:
- `docs/seo-ai-phase1-implementation-checklist.md`

### Phase 2: Competitor and architecture recommendations
Scope:
- competitor domain storage
- competitor comparison snapshots
- site architecture recommendations
- missing page recommendations

Exit criteria:
- a business can compare its site against competitors and receive a page roadmap

### Phase 3: AI briefs and content generation
Scope:
- content brief generation
- metadata suggestions
- service page drafts
- process page drafts
- FAQ drafts
- generated asset lifecycle

Exit criteria:
- a user can turn recommendations into reviewable draft assets

### Phase 4: Reporting and monitoring
Scope:
- report generation
- scheduled rescans
- run-to-run comparison
- improvement/regression summary

Exit criteria:
- a business can monitor site SEO over time and receive periodic reports

---

## 16. Out of Scope

The following items are explicitly out of scope for the first implementation unless separately approved:
- direct CMS publishing
- Google Search Console integration
- Ahrefs or SEMrush integration
- backlink scoring
- full keyword rank tracking
- image optimization pipelines
- schema markup generation beyond simple recommendations
- multi-language SEO
- non-contractor vertical specialization

---

## 17. Open Questions

These should be resolved before deeper implementation begins:
1. Should automated competitor discovery be in MVP or post-MVP?
2. Should crawl execution be synchronous first, or queue-backed from day one?
3. Which AI provider abstraction should be used in mbsrn?
4. Should generated assets live in the DB only, or also as exportable files later?
5. Should service-area page generation be included in MVP or Phase 3+?
6. What approval workflow is required before generated content is considered client-ready?
7. Do we want one shared SEO.ai prompt library document under `docs/` from the start?

---

## 18. Implementation Notes

When implementing this module:
- preserve existing business-scoped API patterns
- keep deterministic extraction separate from AI summarization
- avoid mixing crawl logic directly into route handlers
- create clear repository/service/schema boundaries
- add migration files for new SEO.ai tables
- write focused tests for rule detection and business scoping
- prefer implementation that is incremental and production-clean over demo shortcuts
- avoid speculative overengineering beyond the phases defined here

---

## 19. Definition of Done for Initial SEO.ai Merge

The initial SEO.ai merge is complete when:
- new SEO.ai data models and migrations exist
- site registration endpoints exist
- audit run endpoints exist
- a basic crawl can be executed against a site
- rule-based findings are persisted
- an AI summary can be generated and stored
- tests cover key business scoping and audit finding rules
- docs are added under `docs/`
- README docs list is updated to include the SEO.ai documents
