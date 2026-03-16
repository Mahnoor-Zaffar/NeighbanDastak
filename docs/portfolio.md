# Portfolio Presentation Notes

## 1. Sample portfolio description

NigehbaanDastak is a modular clinic MVP built with FastAPI, SQLAlchemy, and
React. It demonstrates practical backend architecture (service/repository
separation), operational safeguards (audit logs, standardized API errors,
request IDs, rate limiting), and a demo-ready frontend for patient,
appointment, and visit workflows.

## 2. Suggested screenshots

Capture these for GitHub and portfolio pages:

1. Demo auth role selection (`/auth`)
2. Patient list with search and archive status
3. Patient create/edit form validation
4. Appointment list with status filter/actions
5. Create appointment form
6. Create visit form linked to appointment
7. Visit detail page
8. Backend test run output (`48 passed` or latest)
9. Architecture/API summary snippet from docs

## 3. Recommended demo data strategy

Use synthetic records only. Keep names neutral and reproducible:

- 3 active patients
- 1 archived patient
- 2 upcoming appointments
- 1 completed appointment linked to a visit
- 1 standalone visit without appointment

This keeps every major path demonstrable in less than 10 minutes.

## 4. Suggested live demo script (8-10 minutes)

1. Explain architecture in 45 seconds (route -> service -> repository).
2. Show demo auth and role switching.
3. As admin: create patient, edit patient, archive patient.
4. As doctor: list/search patients and create appointment.
5. Change appointment status and create a linked visit.
6. Open visit detail and explain encounter data model.
7. Briefly show standardized error shape and request ID.
8. Show test suite pass output and deployment plan.

## 5. Interview talking points

- why soft archive was chosen for patient records
- why role checks are enforced at route boundaries
- why standardized errors + request IDs improve supportability
- tradeoffs of in-memory rate limiting in MVP
- clear phased roadmap without premature feature complexity

## 6. Portfolio README polish checklist

- short project pitch in first paragraph
- architecture diagram or module map link
- API module summary with role behavior
- local setup in <5 commands
- deployment path and hosting rationale
- known limitations and concrete roadmap
