# SEO Audit Crawl Settings

## Overview

This feature adds a business-scoped, admin-controlled crawl page limit for SEO audits.
The setting controls how many pages an audit crawl is allowed to scan for both manual audits and automation-triggered audits.

## Why This Exists

- The previous default (`25`) was effectively hardcoded in execution paths.
- Businesses need safe control over crawl depth to balance:
  - runtime/cost,
  - crawl coverage,
  - operational consistency across manual and automated runs.
- A DB-backed admin setting was chosen so changes are immediate, tenant-scoped, auditable via existing business settings APIs, and not tied to deploy-time env changes.

## Data Model / Config

### Storage
- Table: `businesses`
- Field: `seo_audit_crawl_max_pages` (`int`, non-null, default `25`)
- Constraint: `5 <= seo_audit_crawl_max_pages <= 250`

### API surface
- Read: `GET /api/businesses/{business_id}`
- Update (admin-only): `PATCH /api/businesses/{business_id}/settings`
- Schema field: `seo_audit_crawl_max_pages`

## Authorization

- Backend remains source of truth.
- Only admin principals can update the setting (`require_credential_manager_principal`).
- Tenant/business scoping is enforced via `TenantContext` + `resolve_tenant_business_id`.

## Runtime Usage

### Manual audit path
- `SEOAuditService.run_audit(...)` resolves effective crawl page limit from the business setting.
- The resolved value is used for crawler execution and persisted on:
  - `seo_audit_runs.max_pages` (legacy field)
  - `seo_audit_runs.crawl_max_pages_used` (explicit observability field)

### Automation path
- `SEOAutomationService` audit step calls `SEOAuditService.run_audit(...)`.
- Automation therefore uses the same business setting automatically (no separate override path).

## Defaults / Bounds

- Default: `25`
- Minimum: `5`
- Maximum: `250`
- If a business does not explicitly update the setting, audits continue using the default value.
- Runtime guard: values outside `5..250` are rejected as invalid configuration.

## Backward Compatibility

- `SEOAuditRunCreateRequest.max_pages` remains in the API payload for compatibility.
- It is deprecated and ignored at runtime.
- Crawl page limit is business-controlled only; per-run overrides are not applied.

## Operational Considerations

- Higher values increase crawl duration and potential load but can improve coverage depth.
- Lower values reduce runtime/cost and can be useful for rapid iteration.
- Because the setting is business-scoped, each tenant can tune crawl depth to its own operational constraints without affecting others.
