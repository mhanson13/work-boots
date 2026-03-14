# SEO.ai Phase 1 Implementation Checklist

Status: Draft  
Owner: Work Boots  
Depends on: `docs/seo-ai-requirements.md`  
Scope: Phase 1 only (baseline audit + AI summary)

---

## 1. Phase 1 Scope Lock

### In scope
- Site registration (business-scoped CRUD)
- Audit run creation and execution
- Deterministic crawl + extraction for small sites
- Rule-based finding generation
- Findings retrieval by audit run
- AI executive summary generation for completed runs

### Out of scope for this checklist
- Competitor analysis
- Architecture recommendations
- Brief/content generation
- Scheduled rescans
- Queue/Celery/Kafka infrastructure

---

## 2. Implementation Decisions (Lock Before Coding)

- [ ] Crawl execution mode for MVP: synchronous request path (with clear service boundary for async later)
- [ ] Crawl limits defaults agreed:
  - [ ] `max_pages` default
  - [ ] `max_depth` default
- [ ] AI provider boundary agreed (interface + mock/dev adapter first)
- [ ] URL restrictions agreed for SSRF safety:
  - [ ] allowed scheme (`http`/`https`)
  - [ ] block localhost/private-network targets for crawl

---

## 3. Data Model + Migration Checklist

### 3.1 New SQLAlchemy models (`app/models/`)
- [ ] `seo_site.py`
- [ ] `seo_audit_run.py`
- [ ] `seo_audit_page.py`
- [ ] `seo_audit_finding.py`
- [ ] `seo_audit_summary.py` (separate from deterministic findings)

### 3.2 Model fields (minimum)
- [ ] `seo_sites`: business-scoped fields from requirements §9.1
- [ ] `seo_audit_runs`: status lifecycle + crawl settings + counts + error summary
- [ ] `seo_audit_pages`: extracted page data (title/meta/h1/h2/word_count/etc.)
- [ ] `seo_audit_findings`: normalized rule findings + severity/category
- [ ] `seo_audit_summaries`: ai summary text + model/prompt metadata + version/timestamps

### 3.3 Relationships and integrity
- [ ] FK: `seo_sites.business_id -> businesses.id`
- [ ] FK: `seo_audit_runs.site_id -> seo_sites.id`
- [ ] FK: `seo_audit_pages.audit_run_id -> seo_audit_runs.id`
- [ ] FK: `seo_audit_findings.audit_run_id -> seo_audit_runs.id`
- [ ] FK: `seo_audit_summaries.audit_run_id -> seo_audit_runs.id`
- [ ] Add `business_id` to all SEO.ai tables (tenant isolation)
- [ ] Add indexes for common reads:
  - [ ] `(business_id, site_id)`
  - [ ] `(business_id, audit_run_id)`
  - [ ] `(business_id, created_at)` where relevant

### 3.4 Alembic
- [ ] Create migration for Phase 1 SEO tables
- [ ] Keep migration safe for existing populated DB
- [ ] Verify `alembic upgrade head` succeeds on local SQLite and Postgres targets

---

## 4. Schema Checklist (`app/schemas/`)

- [ ] `seo_site.py` request/response schemas
- [ ] `seo_audit.py` run/finding/summary schemas
- [ ] Validation:
  - [ ] URL syntax validation
  - [ ] base URL normalization
  - [ ] crawl setting bounds (`max_pages`, `max_depth`)
- [ ] Response schemas exclude internal-only fields and preserve tenant-safe outputs

---

## 5. Repository Checklist (`app/repositories/`)

- [ ] `seo_site_repository.py`
- [ ] `seo_audit_repository.py`
- [ ] Business-scoped methods only for reads/writes:
  - [ ] `get_site_for_business(...)`
  - [ ] `list_sites_for_business(...)`
  - [ ] `create_audit_run(...)`
  - [ ] `list_runs_for_business_site(...)`
  - [ ] `list_findings_for_business_run(...)`
- [ ] Explicit mismatch guards (business/site/run mismatch fails fast)

---

## 6. Service Checklist (`app/services/`)

### 6.1 Site service
- [ ] `seo_sites.py` for site CRUD orchestration
- [ ] Normalize base URL and domain on write
- [ ] Enforce business scoping in all operations

### 6.2 Crawl service
- [ ] `seo_crawler.py` for deterministic crawl
- [ ] Respect crawl limits and include/exclude path filters
- [ ] Same-domain-only mode for MVP default
- [ ] Capture per-page fetch errors without failing entire run

### 6.3 Extraction + rule engine
- [ ] `seo_extractor.py` for page feature extraction
- [ ] `seo_finding_rules.py` for deterministic finding rules
- [ ] Implement minimum Phase 1 rules:
  - [ ] missing title
  - [ ] duplicate title
  - [ ] title too short/long
  - [ ] missing meta description
  - [ ] duplicate meta description
  - [ ] meta too short/long
  - [ ] missing H1
  - [ ] multiple H1
  - [ ] thin content (low word count)
  - [ ] missing canonical

### 6.4 Audit orchestration
- [ ] `seo_audit.py` orchestrates run lifecycle:
  - [ ] `queued -> running -> completed|failed`
  - [ ] page persistence
  - [ ] finding persistence
  - [ ] summary counts persistence
  - [ ] error summary persistence on failure

### 6.5 AI summary service
- [ ] `seo_summary.py` consumes stored findings only
- [ ] Store AI summary separately from deterministic findings
- [ ] Store prompt version + model metadata + timestamps
- [ ] Summary failure does not invalidate completed deterministic run

---

## 7. Integration Boundary Checklist (`app/integrations/`)

- [ ] Add minimal AI provider interface for summaries (mock/dev implementation first)
- [ ] Keep provider-specific code in `integrations/`, not in route handlers
- [ ] Ensure failures raise controlled service-level errors (no raw provider leaks)

---

## 8. API Route Checklist (`app/api/routes/`)

### 8.1 New route module
- [ ] Add `seo.py` route module
- [ ] Register router in:
  - [ ] `app/api/routes/__init__.py`
  - [ ] `app/main.py`

### 8.2 Phase 1 endpoints
- [ ] `GET /api/businesses/{business_id}/seo/sites`
- [ ] `POST /api/businesses/{business_id}/seo/sites`
- [ ] `GET /api/businesses/{business_id}/seo/sites/{site_id}`
- [ ] `PATCH /api/businesses/{business_id}/seo/sites/{site_id}`
- [ ] `POST /api/businesses/{business_id}/seo/sites/{site_id}/audit-runs`
- [ ] `GET /api/businesses/{business_id}/seo/sites/{site_id}/audit-runs`
- [ ] `GET /api/businesses/{business_id}/seo/audit-runs/{run_id}`
- [ ] `GET /api/businesses/{business_id}/seo/audit-runs/{run_id}/findings`
- [ ] `POST /api/businesses/{business_id}/seo/audit-runs/{run_id}/summarize`

### 8.3 Route behavior requirements
- [ ] Tenant context (`TenantContext`) enforced for all routes
- [ ] Do not trust cross-business IDs from request input
- [ ] Route handlers stay thin; business logic in services
- [ ] Clear status codes for validation vs runtime failures

---

## 9. Dependency Injection Checklist (`app/api/deps.py`)

- [ ] Add repository providers for SEO repositories
- [ ] Add service providers for SEO services
- [ ] Wire AI summary integration dependency
- [ ] Keep dependency construction explicit and typed

---

## 10. Testing Checklist (`app/tests/`)

### 10.1 Unit tests
- [ ] URL normalization + validation tests
- [ ] extractor tests (title/meta/headings/word_count)
- [ ] finding-rule tests (rule-by-rule coverage)
- [ ] run status transition tests
- [ ] summary generation persistence tests (including failure path)

### 10.2 API tests
- [ ] business-scoped site CRUD tests
- [ ] cross-business site access rejection tests
- [ ] audit run creation and retrieval tests
- [ ] finding retrieval by run tests
- [ ] summarize endpoint success/failure tests

### 10.3 Security tests
- [ ] tenant isolation checks on all new SEO endpoints
- [ ] SSRF guard tests for blocked host patterns (localhost/private IP)

---

## 11. Logging + Observability Checklist

- [ ] Log audit run lifecycle transitions
- [ ] Log crawl summary (pages discovered/crawled, failures count)
- [ ] Log summary generation failures without leaking sensitive prompt/body data
- [ ] Include run/site/business identifiers in structured log messages

---

## 12. Documentation Checklist

- [ ] Keep `docs/seo-ai-requirements.md` as product requirements source
- [ ] Update README docs list to include this checklist
- [ ] Add `docs/seo-ai-phase1-api-contract.md` (optional but recommended) once schemas stabilize

---

## 13. Suggested PR Slices (Small, Reviewable)

### PR 1: Data foundations
- [ ] Models + migration + repositories
- [ ] Basic site CRUD service + tests

### PR 2: Crawl + findings
- [ ] Crawl service + extraction + rule engine
- [ ] Audit run orchestration + run/findings endpoints + tests

### PR 3: AI summary
- [ ] Summary integration boundary + summarize endpoint + version metadata + tests

### PR 4: Hardening pass
- [ ] Security tests (tenant + SSRF)
- [ ] Logging polish
- [ ] Docs cleanup

---

## 14. Phase 1 Exit Checklist (Definition of Done)

- [ ] A business can create/list/update/get SEO sites
- [ ] A business can create audit runs for a site
- [ ] Audit runs persist deterministic page extraction and findings
- [ ] Run status lifecycle and error summaries work
- [ ] Findings are retrievable by run and business-scoped
- [ ] AI summary can be generated for a completed run and stored separately
- [ ] Cross-business access is blocked in repositories/services/routes
- [ ] Unit and API tests cover core behaviors and failure paths
- [ ] Docs and README are updated
