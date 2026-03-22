# Migration Hygiene (Local Development)

## Overview

Alembic is the schema authority for this repository. Local validation should be run against Alembic-managed state:

```powershell
alembic upgrade head
```

This document explains the known local drift mode around principal/auth tables, how it happens, and how to recover safely.

## Root Cause: `principals.role` Duplicate Column

Observed failure:

- `alembic upgrade head` fails in `0007_principal_roles` with:
  - `column "role" of relation "principals" already exists`

Confirmed drift pattern:

- local DB `alembic_version` is behind (`0005_api_credentials`)
- but schema already contains forward objects from later revisions:
  - `principals.role` (`0007`)
  - principal audit columns (`0009`)
  - `auth_audit_events` table (`0010`)

This is schema drift (version metadata and physical schema no longer match). Fresh databases do not have this issue and migrate cleanly end-to-end.

## Why Fresh Databases Still Pass

On a clean database:

1. Alembic starts from base revisions.
2. Revisions apply in order.
3. `alembic_version` and schema stay aligned.

CI and clean temp-Postgres validation continue to pass with this path.

## Expected Migration Authority

- Alembic revisions under `alembic/versions/` are authoritative.
- `DB_AUTO_CREATE_LOCAL` is now defaulted to `false` for local safety.
- Startup `create_all()` is opt-in only (`DB_AUTO_CREATE_LOCAL=true`) and should be used only for disposable local experiments.

## Remediation Strategy

### Guardrails added for known early drift states

Narrow, explicit migration guards were added in:

- `0007_principal_roles`
- `0008_api_credential_audit_fields`
- `0009_principal_audit_metadata`
- `0010_auth_audit_events`

These guards:

- skip duplicate add/create operations only when the target already exists,
- keep index/FK creation idempotent where expected,
- raise a clear error when existing schema shape is incompatible.

This is intentionally bounded and does not broadly swallow migration errors.

### Developer recovery for drifted local DBs

If local schema/version are materially out of sync, reset is the safest path.

#### Recommended reset (Postgres local)

1. Stop local API processes.
2. Drop and recreate local database.
3. Re-run migrations:

```powershell
alembic upgrade head
```

4. Restart API.

Use this approach instead of force-stamping unknown drifted schemas.

## Validation Checklist

Before local feature work or deploy prep:

1. `alembic upgrade head` on a clean temp Postgres DB.
2. `alembic upgrade head` on local default DB (or after local reset).
3. `pytest`.

If local DB fails due drift and is disposable, reset and re-run steps 1-3.

## Notes

- In-place recovery of heavily drifted local DBs is not guaranteed.
- Production migration history is not rewritten; revisions remain additive and forward-safe.
