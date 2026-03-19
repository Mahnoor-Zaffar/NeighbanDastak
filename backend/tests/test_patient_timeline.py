from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.core.rbac import Role
from app.db.models.patient import Patient


ADMIN_HEADERS = {"X-Demo-Role": "admin"}
DOCTOR_ROLE_HEADERS = {"X-Demo-Role": "doctor"}
RECEPTIONIST_HEADERS = {"X-Demo-Role": "receptionist"}


def _doctor_headers(user_id: str) -> dict[str, str]:
    return {"X-Demo-Role": "doctor", "X-Demo-User-Id": user_id}


def build_patient_payload(record_number: str = "PAT-TL-2001") -> dict[str, str]:
    return {
        "record_number": record_number,
        "first_name": "Maha",
        "last_name": "Qazi",
        "date_of_birth": "1990-02-21",
        "email": f"{record_number.lower()}@example.com",
        "phone": "+1 555 7701",
        "city": "Karachi",
        "notes": "Timeline test patient.",
    }


def create_patient(client, record_number: str) -> dict:
    response = client.post("/api/v1/patients", json=build_patient_payload(record_number), headers=ADMIN_HEADERS)
    assert response.status_code == 201
    return response.json()


def create_appointment(client, patient_id: str, headers: dict[str, str] | None = None) -> dict:
    response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "scheduled_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "reason": "Timeline follow-up",
            "notes": "Initial appointment scheduling.",
        },
        headers=headers or DOCTOR_ROLE_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def create_visit(client, patient_id: str, appointment_id: str) -> dict:
    response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "started_at": datetime.now(UTC).isoformat(),
            "complaint": "Persistent cough",
            "diagnosis_summary": "Acute bronchitis",
            "notes": "Timeline visit note.",
        },
        headers=DOCTOR_ROLE_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def create_prescription(client, patient_id: str, visit_id: str, doctor_id: str) -> dict:
    response = client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": patient_id,
            "visit_id": visit_id,
            "doctor_id": doctor_id,
            "diagnosis_summary": "Acute bronchitis",
            "notes": "Complete full course.",
            "items": [
                {
                    "medicine_name": "Amoxicillin",
                    "dosage": "500mg",
                    "frequency": "Every 8 hours",
                    "duration": "5 days",
                    "instructions": "After meals",
                }
            ],
        },
        headers=DOCTOR_ROLE_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def assign_appointment_to_doctor(client, appointment_id: str, doctor_id: str) -> None:
    response = client.post(
        f"/api/v1/appointments/{appointment_id}/check-in",
        json={"assigned_doctor_id": doctor_id},
        headers=RECEPTIONIST_HEADERS,
    )
    assert response.status_code == 200


def test_timeline_aggregates_mixed_events_and_orders_descending(client, create_user) -> None:
    doctor_user = create_user(
        email="doctor-timeline@example.com",
        full_name="Dr. Timeline",
        role=Role.DOCTOR,
        specialty="Pulmonology",
        license_number="ND-TL-0001",
    )
    patient = create_patient(client, "PAT-TL-2001")
    appointment = create_appointment(client, patient["id"])
    assign_appointment_to_doctor(client, appointment["id"], str(doctor_user.id))
    update_response = client.patch(
        f"/api/v1/appointments/{appointment['id']}",
        json={"status": "completed"},
        headers=DOCTOR_ROLE_HEADERS,
    )
    assert update_response.status_code == 200
    visit = create_visit(client, patient["id"], appointment["id"])
    prescription = create_prescription(client, patient["id"], visit["id"], str(doctor_user.id))

    timeline_response = client.get(
        f"/api/v1/patients/{patient['id']}/timeline",
        headers=_doctor_headers(str(doctor_user.id)),
    )
    assert timeline_response.status_code == 200
    body = timeline_response.json()
    assert body["sort_order"] == "desc"
    assert body["patient_id"] == patient["id"]
    assert body["total"] == len(body["items"])
    assert body["total"] >= 5

    event_types = [event["event_type"] for event in body["items"]]
    assert "patient_created" in event_types
    assert "appointment_scheduled" in event_types
    assert "appointment_completed" in event_types
    assert "visit_created" in event_types
    assert "prescription_created" in event_types

    prescription_events = [event for event in body["items"] if event["event_type"] == "prescription_created"]
    assert prescription_events
    assert prescription_events[0]["related_entity_id"] == prescription["id"]
    assert prescription_events[0]["actor_name"] == "Dr. Timeline"

    timestamps = [datetime.fromisoformat(event["event_timestamp"]) for event in body["items"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_timeline_authorization_behavior(client, create_user, unsupported_role_headers) -> None:
    doctor_allowed_user = create_user(
        email="doctor-timeline-access-a@example.com",
        full_name="Dr. Timeline Access A",
        role=Role.DOCTOR,
        specialty="Internal Medicine",
        license_number="ND-TL-0002",
    )
    doctor_blocked_user = create_user(
        email="doctor-timeline-access-b@example.com",
        full_name="Dr. Timeline Access B",
        role=Role.DOCTOR,
        specialty="Dermatology",
        license_number="ND-TL-0003",
    )

    patient = create_patient(client, "PAT-TL-2002")
    patient_id = patient["id"]
    appointment = create_appointment(client, patient_id)
    assign_appointment_to_doctor(client, appointment["id"], str(doctor_allowed_user.id))

    missing_auth = client.get(f"/api/v1/patients/{patient_id}/timeline")
    assert missing_auth.status_code == 401
    assert missing_auth.json()["error"]["code"] == "http_401"

    unsupported_role = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=unsupported_role_headers)
    assert unsupported_role.status_code == 403
    assert unsupported_role.json()["error"]["message"] == "Unsupported role"

    doctor_missing_identity = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=DOCTOR_ROLE_HEADERS)
    assert doctor_missing_identity.status_code == 403
    assert doctor_missing_identity.json()["error"]["message"] == "Doctor identity is required"

    doctor_allowed = client.get(
        f"/api/v1/patients/{patient_id}/timeline",
        headers=_doctor_headers(str(doctor_allowed_user.id)),
    )
    assert doctor_allowed.status_code == 200

    doctor_forbidden = client.get(
        f"/api/v1/patients/{patient_id}/timeline",
        headers=_doctor_headers(str(doctor_blocked_user.id)),
    )
    assert doctor_forbidden.status_code == 403
    assert doctor_forbidden.json()["error"]["message"] == "Doctors can only view timelines for their assigned patients"

    receptionist_allowed = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=RECEPTIONIST_HEADERS)
    assert receptionist_allowed.status_code == 200


def test_timeline_returns_404_for_unknown_patient(client) -> None:
    response = client.get("/api/v1/patients/00000000-0000-0000-0000-000000000000/timeline", headers=ADMIN_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Patient not found"


def test_timeline_can_be_empty_when_no_events_exist(client, db_session) -> None:
    patient = Patient(
        record_number="PAT-TL-EMPTY",
        first_name="Empty",
        last_name="Timeline",
        date_of_birth=date(1989, 6, 12),
        email="empty.timeline@example.com",
        phone="+1 555 8812",
        city="Lahore",
        notes="Inserted directly to bypass audit-created event.",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    response = client.get(f"/api/v1/patients/{patient.id}/timeline", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["patient_id"] == str(patient.id)
    assert body["sort_order"] == "desc"
    assert body["total"] == 0
    assert body["items"] == []
