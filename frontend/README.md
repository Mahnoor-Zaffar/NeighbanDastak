# NigehbaanDastak Frontend

Phase 6 keeps the UI intentionally simple and demo-oriented. It focuses on
clear flows for current backend modules only: auth simulation, patients,
appointments, and visits.

## Implemented routes

- `/auth` demo role selection (`admin` or `doctor`)
- `/appointments` appointment list, status update, and delete (admin only)
- `/appointments/new` create appointment
- `/visits/new` create visit (optionally linked to an appointment)
- `/visits/:visitId` visit detail
- `/patients` patient list + search + archive (admin only)
- `/patients/new` create patient (admin only)
- `/patients/:patientId` patient detail
- `/patients/:patientId/edit` edit patient (admin only)

## Demo flow

1. Open frontend and choose a role on `/auth`.
2. Create or review patients.
3. Create appointments for patients.
4. Create visits directly or from an appointment.
5. Switch role from the sidebar/mobile menu to validate permission boundaries.

## Local run

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if your backend is not on the default
`http://localhost:8000/api/v1`.

## Current limitations by design

- No production authentication yet (demo role simulation only)
- No reminders/notifications/calendar UX
- No prescriptions, billing, analytics, attachments, or patient portal views
