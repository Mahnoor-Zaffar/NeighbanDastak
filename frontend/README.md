# NigehbaanDastak Frontend

Phase 6 keeps the UI intentionally simple and demo-oriented. It focuses on
clear flows for current backend modules only: auth simulation, patients,
appointments, visits, and prescriptions.

## Implemented routes

- `/auth` demo role selection (`admin`, `doctor`, or `receptionist`)
- `/appointments` appointment list, status update, and delete (admin only)
- `/appointments/new` create appointment
- `/visits/new` create visit (optionally linked to an appointment)
- `/visits/:visitId` visit detail
- `/prescriptions/new?patient_id=...&visit_id=...` create prescription from visit context
- `/prescriptions/:prescriptionId` prescription detail + edit
- `/print/prescriptions/:prescriptionId` A4 print/export layout (Print or Save as PDF)
- `/patients` patient list + search + archive (admin only)
- `/patients/new` create patient (admin only)
- `/patients/:patientId` patient detail
- `/patients/:patientId/edit` edit patient (admin only)

## Demo flow

1. Open frontend and choose a role on `/auth`.
2. Create or review patients.
3. Create appointments for patients.
4. Create visits directly or from an appointment.
5. Create prescriptions from visit detail and review them from visit/patient pages.
6. Open prescription detail and use Print / Save PDF.
7. Switch role from the sidebar/mobile menu to validate permission boundaries.

## Local run

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if your backend is not on the default
`http://localhost:8000/api/v1`.

## Frontend confidence checks

```bash
cd frontend
npm run build
```

This project currently relies on TypeScript + production build checks as the
practical frontend confidence baseline for MVP scope.

## Current limitations by design

- No production authentication yet (demo role simulation only)
- No reminders/notifications/calendar UX
- No server-side PDF generation pipeline yet (browser print/save-PDF workflow is implemented)

## Presentation note

For screenshot checklist and demo walkthrough script, see:

- `../docs/portfolio.md`
