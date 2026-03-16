# NigehbaanDastak

NigehbaanDastak is a backend-first portfolio project for a small-clinic health
records MVP. The current codebase includes patient, scheduling, and Phase 5
security hardening (audit logs + validation/API hardening), and intentionally
stops before prescriptions, notifications, billing, analytics, attachments, or
patient self-service modules.

## Current scope

- FastAPI backend foundation plus patient, appointment, and visit modules
- SQLAlchemy models for patient records, appointments, and encounters
- modular repository and service layers for patient and scheduling flows
- role-based API permissions using demo roles for MVP review
- simple appointment status handling and visit creation linked to patients
- audit logging for sensitive state changes
- standardized API error responses with request IDs
- basic in-memory write-rate limiting for abuse protection
- Phase 6 frontend demo with role-aware navigation, patient/appointment/visit pages, and basic loading/empty/error handling
- Docker Compose for local development

## Local development

1. Review `infra/.env.example`.
   All backend variables are namespaced with `ND_` to avoid host-environment collisions.
2. From `infra/`, run `docker compose up --build`.
3. Apply migrations: `docker compose exec backend alembic upgrade head`
4. Use the demo role header for backend requests:
   `X-Demo-Role: admin` for patient lifecycle and appointment deletion,
   `X-Demo-Role: doctor` for read/search plus appointment and visit capture.
5. Backend health endpoint: `http://localhost:8000/api/v1/health`
6. Frontend demo: `http://localhost:5173`

## Backend commands

Run from [`backend`](/Users/mac/Documents/Software%20Engineering%20Folder/Portfolio%20Projects/NeighbaanDastak/backend):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
alembic upgrade head
pytest
```

## Next approved implementation steps

1. replace demo-role headers with real auth integration
2. prescriptions and downstream workflow modules
3. notifications and operational workflows
