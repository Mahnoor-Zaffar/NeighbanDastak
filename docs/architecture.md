# Security Hardening Architecture

## Current backend modules

- `app/core`: settings, logging, RBAC
- `app/db/models`: SQLAlchemy patient, appointment, and visit models
- `app/db/models/audit_log.py`: SQLAlchemy audit log model
- `app/repositories`: patient, appointment, visit, and audit-log data access
- `app/services`: patient and scheduling business logic + audit capture
- `app/api/routes`: health, patient, appointment, and visit endpoints
- `app/api/deps`: demo-role permission dependencies
- `app/core/errors.py`: standardized error response handlers
- `app/core/middleware.py`: request ID + in-memory rate limiting middleware

## Scope intentionally deferred

- prescriptions
- notifications
- billing
- analytics
- attachments
- patient self-service portals

## Security assumptions and limitations

- Demo-role headers are still used instead of production authentication.
- Audit logging covers sensitive state changes but not external SIEM shipping.
- Rate limiting is intentionally lightweight and single-instance only.
