# API (with security hardening)

Base path: `/api/v1`

## System

- `GET /health`

## Patients

- `GET /patients`
- `POST /patients`
- `GET /patients/{patient_id}`
- `PATCH /patients/{patient_id}`
- `DELETE /patients/{patient_id}`

## Appointments

- `GET /appointments`
- `POST /appointments`
- `GET /appointments/{appointment_id}`
- `PATCH /appointments/{appointment_id}`
- `DELETE /appointments/{appointment_id}`

## Visits

- `POST /visits`
- `GET /visits/{visit_id}`
- `PATCH /visits/{visit_id}`

## Notes

- This phase uses the `X-Demo-Role` header instead of full authentication.
- `admin` can manage patients, manage appointment statuses, and delete appointments.
- `doctor` can read/search patients, create/update appointments, and create/read visits.
- Error responses are standardized as `{ error: { code, message, details? }, request_id }`.
- Request IDs are emitted in the `X-Request-ID` response header.
- Write operations are protected by basic in-memory rate limiting.
- Prescriptions, notifications, billing, analytics, attachments, and patient portal APIs are intentionally not implemented yet.
