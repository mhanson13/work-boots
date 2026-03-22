# MBSRN Operator Platform

MBSRN (My Business Sucks Right Now) is a FastAPI + Next.js platform for SEO operations, competitor intelligence, and operator-driven recommendation workflows.

## What Is Shipped
- Business-scoped operator auth (Google identity exchange to internal principal authorization)
- SEO site management, deterministic audit runs, and findings/reporting
- Competitor intelligence runs and comparison reporting
- AI-assisted competitor profile draft generation with strict review gating
- Deterministic recommendation runs with AI narrative overlays and bounded tuning suggestions
- Manual, confirmed tuning apply flow (no automatic settings mutation)

## Trust Boundary
AI features are advisory only:

`AI generation -> draft/recommendation artifacts -> operator review -> explicit action`

The backend remains authoritative for authorization, validation, and settings bounds.

## Repository Structure
```text
app/                    FastAPI app (routes, services, models, repositories, tests)
alembic/                Database migrations
docs/                   Canonical docs index, feature docs, operations and development guides
frontend/operator-ui/   Next.js operator workspace
infra/                  Kubernetes manifests/overlays
scripts/                Local/dev and bootstrap scripts
```

## Quick Start
### Backend
```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Windows helper:
```powershell
.\scripts\run_api.bat
```

### Operator UI
```powershell
cd frontend/operator-ui
npm ci
npm run dev
```

Required local frontend env values in `frontend/operator-ui/.env.local`:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

## Tests and Quality
Backend tests live in `app/tests` and are discovered via `pytest.ini`.

### Backend
```powershell
pytest
pytest --cov=app --cov-report=term-missing --cov-report=xml
```

### Frontend
```powershell
cd frontend/operator-ui
npm test -- --runInBand
npm run lint
npm run typecheck
npm run build
```

### CI Alignment
- Backend CI: `.github/workflows/backend-ci.yml`
- Frontend CI: `.github/workflows/frontend-ci.yml`

Coverage and test suites include SEO audit/crawl behavior, competitor candidate quality/deduplication, recommendation+narrative APIs, tuning preview/attribution flows, and business settings validation.

## Documentation
Start with [docs/README.md](docs/README.md) for canonical navigation.

## Branding
- Product: **MBSRN (My Business Sucks Right Now)**
- Frontend surface: **Operator Workspace**

Legacy lead-intake and early exploration docs are retained under `docs/archive/` for historical reference and are not part of the primary implementation path.
