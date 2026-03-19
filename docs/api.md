# API Module Summary

Base path: `/api/v1`

## Authentication model (MVP)

This phase uses a demo-role header:

- `X-Demo-Role: admin`
- `X-Demo-Role: doctor`
- `X-Demo-Role: receptionist`

Doctor-scoped endpoints also require:

- `X-Demo-User-Id: <doctor_uuid>`

No production auth/token flow is implemented yet.
For demo login/bootstrap, use the auth endpoints below.

## Module endpoints

### System

- `GET /health`

### Demo Auth

- `GET /auth/demo/doctors`
- `POST /auth/demo/login`
- `GET /auth/demo/current-user`

### Patients

- `GET /patients`
- `POST /patients`
- `GET /patients/{patient_id}`
- `PATCH /patients/{patient_id}`
- `DELETE /patients/{patient_id}` (soft archive)

### Appointments

- `GET /appointments`
- `POST /appointments`
- `GET /appointments/{appointment_id}`
- `PATCH /appointments/{appointment_id}`
- `DELETE /appointments/{appointment_id}`

### Visits

- `POST /visits`
- `GET /visits/{visit_id}`
- `PATCH /visits/{visit_id}`

## Role behavior summary

- `admin`: full patient lifecycle, appointment CRUD including delete, visit CRUD actions
- `doctor`: read/search patients, create/update appointments, create/read/update visits, doctor-scoped follow-ups/queue/analytics
- `receptionist`: read/search and operational queue access, no clinical write actions

## Response conventions

- standardized errors: `{ "error": { "code", "message", "details?" }, "request_id" }`
- `X-Request-ID` response header mirrors request context
- validation errors use `error.code = "validation_error"`

## Deferred APIs (intentional)

- prescriptions
- notifications
- billing
- analytics
- attachments
- patient self-service portals
