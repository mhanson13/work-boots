# Operator UI And Google Auth

## Overview
Work Boots now includes a standalone operator UI app in `frontend/operator-ui` built with Next.js + React + TypeScript.

The FastAPI monolith remains the system of record. The UI consumes existing business-scoped APIs and does not reimplement backend business logic.

## Authentication and Authorization Model

1. User authenticates with Google (OIDC ID token).
2. UI calls `POST /api/auth/google/exchange`.
3. Backend verifies Google token via JWKS signature + claim validation (`sub`, issuer, audience, email_verified policy).
4. Backend resolves `principal_identities` mapping (`provider=google`, `provider_subject=sub`).
5. Backend validates mapped internal principal is active.
6. Backend issues signed app JWT access + refresh tokens.
7. API authorization remains internal and business-scoped via principal/business role checks.

Key boundary:
- Google answers identity (`who is the user?`).
- Work Boots answers authorization (`what can the user do?`).

## Google Login Vs Google Business Profile Authorization

These are two distinct flows and remain intentionally separated:

1. Google sign-in (OIDC) for Work Boots session authentication:
   - UI obtains a Google ID token.
   - API verifies identity and issues Work Boots app session tokens.
   - No Google API resource access is granted by this step.
2. Google Business Profile connection (OAuth authorization code flow):
   - Authenticated Work Boots user explicitly starts a connect flow.
   - API requests `https://www.googleapis.com/auth/business.manage`.
   - API exchanges code server-side and stores provider credentials for future Google API calls.

Why this separation matters:
- OIDC login identifies the user for Work Boots access control.
- OAuth authorization grants delegated Google API access for Business Profile operations.
- Login success alone is not sufficient to call Business Profile APIs.

## Backend Data Model Additions

`principal_identities`
- Maps external identity providers to internal principals.
- Enforces one provider subject to one principal mapping.
- Includes active state and `last_authenticated_at` tracking.

`provider_oauth_states`
- Stores one-time, expiring OAuth `state` hashes for replay-resistant callback handling.

`provider_connections`
- Stores tenant-scoped provider connection metadata and encrypted OAuth tokens for API integrations.

## Auth Endpoints

- `POST /api/auth/google/exchange`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Business admin identity mapping endpoints:
- `GET /api/businesses/{business_id}/principal-identities`
- `POST /api/businesses/{business_id}/principal-identities`
- `POST /api/businesses/{business_id}/principal-identities/{identity_id}/activate`
- `POST /api/businesses/{business_id}/principal-identities/{identity_id}/deactivate`

Business Profile authorization endpoints:
- `POST /api/integrations/google/business-profile/connect/start`
- `GET /api/integrations/google/business-profile/connect/callback`
- `GET /api/integrations/google/business-profile/connection`
- `POST /api/integrations/google/business-profile/disconnect`

## Google Business Profile Connect Flow

1. Authenticated user calls `POST /api/integrations/google/business-profile/connect/start`.
2. API validates tenant/principal context, generates one-time `state`, and returns Google authorization URL.
3. User grants consent for `https://www.googleapis.com/auth/business.manage`.
4. Google redirects to configured callback URI with `code` + `state`.
5. API validates `state`, exchanges code server-side, and persists encrypted provider credentials.
6. API integration calls can later use stored credentials and refresh tokens server-side.

Security controls in this flow:
- one-time state hash persistence with TTL and consume-on-callback behavior
- fixed, server-configured redirect URI
- no access/refresh token exposure in browser API responses
- encrypted token persistence at rest
- denial/missing-refresh/replay/refresh-failure handling with auth audit events

## UI Scope (Initial Operator Surface)

Implemented pages:
- Dashboard
- Sites
- Audit runs
- Competitor intelligence sets
- Recommendations
- Automation run history

The UI uses a typed API client and environment-based API configuration:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

## Required Environment Configuration

Authentication (existing Google sign-in):
- `GOOGLE_AUTH_ENABLED`
- `GOOGLE_OIDC_CLIENT_ID`
- `GOOGLE_OIDC_JWKS_URL`
- `GOOGLE_OIDC_REQUIRE_EMAIL_VERIFIED`
- `APP_SESSION_SECRET`

Business Profile authorization (new integration connect flow):
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_BUSINESS_PROFILE_REDIRECT_URI`
- `GOOGLE_OAUTH_TOKEN_ENCRYPTION_SECRET`
- `GOOGLE_BUSINESS_PROFILE_STATE_TTL_SECONDS`

`GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` default to the OIDC values when omitted, but dedicated OAuth client credentials are recommended for production clarity.

## Google Cloud Setup Requirements For Business Profile

Before connect flow can succeed in a real environment:
- Enable Business Profile related APIs in the Google Cloud project used by your OAuth client.
- Configure OAuth consent screen and app publishing/test-user policy as required by your org and Google policy.
- Ensure OAuth client redirect URI includes:
  - `<API_BASE_URL>/api/integrations/google/business-profile/connect/callback`
- Confirm your Google account/project has required Business Profile API access/approval.

If API access is not enabled/approved, OAuth may succeed but downstream Business Profile API calls will fail.

## Security Notes

- Google identity alone does not grant access.
- Access requires explicit mapping to an internal principal.
- Inactive principal identities are rejected.
- Inactive principals are rejected.
- Tenant/business scope enforcement remains in existing `TenantContext` + repository/service lineage protections.
- Business Profile connection credentials are tenant-scoped and server-managed (not browser-managed).
- Refresh tokens are required for durable API access; if Google does not return one, reconnect with consent.
- Refresh token issuance behavior is controlled by Google policy and prior consent history; reconnect may be required.
- Operator UI session storage policy:
  - access token: `sessionStorage`
  - refresh token: in-memory only (not browser-persistent)
  - principal metadata: `sessionStorage`
  - sign-out calls `/api/auth/logout` and clears local session state
