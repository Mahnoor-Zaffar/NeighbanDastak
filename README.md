# NigehbaanDastak

NigehbaanDastak is a clinic-management MVP built for portfolio and interview
presentation. It focuses on practical backend architecture, clear API behavior,
security-minded defaults, and a demo-ready frontend.

## What Is Implemented

- patient management (CRUD + archive)
- appointment management (CRUD + status transitions)
- visit/encounter management (linked to patient and optional appointment)
- role-based permissions via demo roles (`admin`, `doctor`)
- audit logging for sensitive write actions
- standardized API errors with request IDs
- basic write-rate limiting
- React demo UI for auth simulation + patient/appointment/visit flows

Intentionally deferred:

- prescriptions
- notifications
- billing
- analytics
- attachments
- patient self-service portals

## Architecture Summary

- backend: FastAPI + SQLAlchemy + Alembic
- pattern: route -> service -> repository
- frontend: React + TypeScript + React Router
- testing: pytest API/integration/unit coverage for critical flows

Detailed module architecture:

- [`docs/architecture.md`](docs/architecture.md)

## API Module Summary

Base path: `/api/v1`

- system: `/health`
- patients: list/create/detail/update/archive
- appointments: list/create/detail/update/delete
- visits: create/detail/update

Role behavior and response conventions:

- [`docs/api.md`](docs/api.md)

## Local Setup (Clean Path)

### Option A: Docker Compose (recommended)

```bash
cd infra
cp .env.example .env
docker compose up --build
docker compose exec backend alembic upgrade head
```

- backend: `http://localhost:8000/api/v1`
- frontend: `http://localhost:5173`
- health: `http://localhost:8000/api/v1/health`

### Option B: Run services separately

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Tests

Run all backend tests:

```bash
cd backend
python3 -m pytest
```

Targeted confidence suites:

```bash
python3 -m pytest tests/test_auth_api.py tests/test_integration_flows.py
python3 -m pytest tests/test_schema_validation.py tests/test_audit_service_unit.py
```

Frontend build confidence check:

```bash
cd frontend
npm run build
```

## Deployment Plan

Detailed plan:

- [`docs/deployment.md`](docs/deployment.md)

Quick recommendation for lowest complexity/cost:

1. Frontend on Vercel
2. Backend on Railway (or Render)
3. Postgres on same backend vendor

Why:

- minimal ops overhead for solo maintenance
- straightforward environment variable management
- easy interview explanation

## Environment Separation

- local: `infra/.env.example`
- production template: `infra/.env.production.example`

Core production settings:

- `ND_ENVIRONMENT=production`
- `ND_DEBUG=false`
- `ND_DATABASE_URL=<managed postgres url>`
- `ND_CORS_ORIGINS=["https://<frontend-domain>"]`

## Demo Account and Data Strategy

This MVP uses role simulation, not user accounts.

- `admin`: patient lifecycle + appointment delete
- `doctor`: patient read/search + appointment/visit capture

Use synthetic data only. Suggested demo baseline:

- 3 active patients
- 1 archived patient
- 2 upcoming appointments
- 1 completed appointment linked to a visit

## Portfolio Presentation

Use this as your portfolio/project blurb:

> Modular clinic MVP with FastAPI + React, covering patient, appointment, and
> visit workflows, with audit logging, standardized API error handling, and
> practical test coverage for critical flows.

Suggested screenshots and live demo script:

- [`docs/portfolio.md`](docs/portfolio.md)

## Known Limitations

- demo-role header auth only (no production auth/session model yet)
- in-memory rate limiting (single instance)
- no background workers
- no file attachments or prescriptions module
- no advanced analytics/dashboarding

## Future Roadmap

1. replace demo-role auth with real authentication and user model
2. prescriptions and medication workflow module
3. notifications/reminders and async task processing
4. stronger production controls (distributed rate limiting, observability, CI/CD)

## Documentation Index

- architecture: [`docs/architecture.md`](docs/architecture.md)
- API summary: [`docs/api.md`](docs/api.md)
- deployment guide: [`docs/deployment.md`](docs/deployment.md)
- portfolio notes/demo script: [`docs/portfolio.md`](docs/portfolio.md)
