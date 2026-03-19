# NigehbaanDastak Backend

This package currently contains the foundation plus patient and scheduling phases:

- FastAPI application entrypoint
- environment-driven configuration
- SQLAlchemy engine and session management
- Alembic migration wiring
- shared base model mixins
- logging configuration
- health check endpoint
- patient model and migration
- patient repository and service layer
- patient CRUD and search endpoints
- appointment model and status workflow
- visit/encounter model linked to patients and optional appointments
- appointment and visit repositories/services/routes
- role-based permissions via demo-role headers (`admin` and `doctor`)
- demo auth bootstrap endpoints for doctor-profile-aware sessions
- audit log persistence for sensitive actions
- standardized API error payloads with request IDs
- basic in-memory write-rate limiting

Business modules such as prescriptions, notifications, billing, analytics,
attachments, and patient portals remain postponed until later phases are approved.

Configuration variables are namespaced with `ND_` so local shell variables such
as `DEBUG` do not leak into the app unexpectedly.

## Security assumptions (MVP)

- Authentication is still demo-role header based, not production auth.
- Audit logs are persisted in the app database and intentionally store only
  sanitized metadata.
- Rate limiting is process-local in memory; it is suitable for a single MVP node
  and not distributed deployments.

## Testing

Run from the `backend/` directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Targeted test runs:

```bash
pytest tests/test_auth_api.py tests/test_integration_flows.py
pytest tests/test_schema_validation.py tests/test_audit_service_unit.py
```

Test database notes:

- tests use an isolated in-memory SQLite database (`sqlite://`) with `StaticPool`
- schema is dropped/recreated around each test for repeatable runs
- settings cache is cleared for each test so environment overrides do not leak

## Deployment note

For environment separation and hosting recommendations, see:

- `../docs/deployment.md`
