# API Module Summary

Base path: `/api/v1`

## Authentication model (MVP)

This phase uses a demo-role header:

- `X-Demo-Role: admin`
- `X-Demo-Role: doctor`

No production auth/token flow is implemented yet.

## Module endpoints

### System

- `GET /health`

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
- `doctor`: read/search patients, create/update appointments, create/read/update visits

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
