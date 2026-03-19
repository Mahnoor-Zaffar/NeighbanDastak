# Patient Timeline Phase 1 (Backend)

## Decision: Normalized Timeline Event Model

Phase 1 uses a single normalized event envelope for all patient history entries:

- `id`
- `event_type`
- `event_timestamp`
- `title`
- `subtitle`
- `actor_name`
- `related_entity_type`
- `related_entity_id`
- `metadata`

Rationale:

- keeps API response stable across heterogeneous source tables
- lets UI render mixed events without type-specific API branching
- supports incremental event-type additions in future phases by appending new `event_type` values and metadata

## Aggregation Strategy

The timeline service pragmatically aggregates from existing tables and audit logs:

- patient profile creation (`audit_logs` where `action=patient.create`)
- appointment scheduling (`appointments.created_at`)
- appointment status changes (`audit_logs` where `action=appointment.status_change`)
- fallback appointment terminal status events from appointment rows when audit status-change log is absent
- visit creation (`visits.created_at`)
- prescription creation (`prescriptions.created_at`)

No event-sourcing subsystem is introduced in this phase.

## Endpoint

- `GET /api/v1/patients/{patient_id}/timeline`

Response:

- `patient_id`
- `sort_order` (`desc`)
- `items` (normalized events, newest first)
- `total`

Ordering:

- deterministic descending sort by `(event_timestamp, id)`

## Authorization Rules

- `admin`: can view all patient timelines
- `receptionist`: allowed per current project read-access behavior
- `doctor`:
  - must provide `X-Demo-User-Id`
  - must be an active doctor account
  - can view timeline only if assigned to that patient through at least one appointment (`appointments.assigned_doctor_id`)

## Tests Added/Updated

- mixed event aggregation and ordering
- authorization behavior:
  - missing auth
  - unsupported role
  - doctor missing identity
  - doctor assigned allowed
  - doctor not assigned denied
  - receptionist allowed
- patient not found
- empty timeline
