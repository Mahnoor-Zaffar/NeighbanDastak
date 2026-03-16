# Architecture Summary (MVP)

## System shape

NigehbaanDastak is a modular FastAPI backend with a lightweight React frontend.
The backend follows a route -> service -> repository pattern to keep business
logic and data access separated and testable.

## Backend module map

- `app/main.py`: app factory, middleware wiring, API router mount
- `app/core`: config, logging, RBAC enums, error handlers, request/rate-limit middleware
- `app/db`: SQLAlchemy session + shared base model
- `app/db/models`: patient, appointment, visit, and audit log entities
- `app/schemas`: Pydantic request/response validation
- `app/repositories`: persistence and query logic per entity
- `app/services`: domain logic for patient, appointment, visit, and audit flows
- `app/api/routes`: HTTP endpoints grouped by module
- `app/api/deps`: demo-role access dependency

## Frontend module map

- `src/app`: router + API client
- `src/components`: shared layout, auth gate, forms
- `src/pages`: patient, appointment, visit, and demo auth pages

## Request flow

1. Request enters middleware (request ID, rate limit).
2. Route validates payload and permissions.
3. Service applies business rules and audit events.
4. Repository reads/writes SQLAlchemy models.
5. Standardized JSON response or standardized error shape is returned.

## Security posture for MVP

- demo roles (`X-Demo-Role`) are used instead of production auth
- request IDs are attached to all responses
- write endpoints are protected by in-memory rate limiting
- sensitive actions write audit events with sanitized metadata

## Scope intentionally deferred

- prescriptions
- notifications
- billing
- analytics
- attachments
- patient self-service portals
