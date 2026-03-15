from __future__ import annotations

from datetime import UTC, datetime, timedelta


ADMIN_HEADERS = {"X-Demo-Role": "admin"}
DOCTOR_HEADERS = {"X-Demo-Role": "doctor"}


def build_patient_payload(record_number: str = "PAT-2001") -> dict[str, str]:
    return {
        "record_number": record_number,
        "first_name": "Sara",
        "last_name": "Iqbal",
        "date_of_birth": "1991-08-03",
        "email": f"{record_number.lower()}@example.com",
        "phone": "+1 555 0201",
        "city": "Lahore",
        "notes": "Phase 4 patient.",
    }


def build_appointment_payload(patient_id: str) -> dict[str, str]:
    return {
        "patient_id": patient_id,
        "scheduled_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "reason": "Routine follow-up",
        "notes": "Bring latest lab reports.",
    }


def test_doctor_can_create_and_list_appointments(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload(), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]

    create_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "scheduled"

    list_response = client.get("/api/v1/appointments", headers=DOCTOR_HEADERS)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1


def test_appointment_requires_role_header(client) -> None:
    response = client.get("/api/v1/appointments")
    assert response.status_code == 401


def test_appointment_status_transition_is_enforced(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2002"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    create_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = create_response.json()["id"]

    complete_response = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={"status": "completed"},
        headers=DOCTOR_HEADERS,
    )
    assert complete_response.status_code == 200

    invalid_transition_response = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={"status": "scheduled"},
        headers=DOCTOR_HEADERS,
    )
    assert invalid_transition_response.status_code == 409


def test_appointment_rejects_past_schedule_time(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2010"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    payload = build_appointment_payload(patient_id)
    payload["scheduled_for"] = (datetime.now(UTC) - timedelta(days=1)).isoformat()

    response = client.post("/api/v1/appointments", json=payload, headers=DOCTOR_HEADERS)
    assert response.status_code == 422


def test_doctor_cannot_delete_appointment(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2003"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    create_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/appointments/{appointment_id}", headers=DOCTOR_HEADERS)
    assert delete_response.status_code == 403


def test_admin_can_delete_appointment_without_visit(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2008"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    create_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/appointments/{appointment_id}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 204


def test_create_visit_marks_appointment_completed(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2004"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    appointment_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = appointment_response.json()["id"]

    visit_response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "started_at": datetime.now(UTC).isoformat(),
            "complaint": "Fever and cough",
            "diagnosis_summary": "Viral upper respiratory infection",
            "notes": "Hydration and rest advised.",
        },
        headers=DOCTOR_HEADERS,
    )
    assert visit_response.status_code == 201
    visit_id = visit_response.json()["id"]

    appointment_after_visit = client.get(f"/api/v1/appointments/{appointment_id}", headers=DOCTOR_HEADERS)
    assert appointment_after_visit.status_code == 200
    assert appointment_after_visit.json()["status"] == "completed"

    visit_detail = client.get(f"/api/v1/visits/{visit_id}", headers=DOCTOR_HEADERS)
    assert visit_detail.status_code == 200
    assert visit_detail.json()["diagnosis_summary"] == "Viral upper respiratory infection"


def test_visit_rejects_mismatched_appointment_patient(client) -> None:
    patient_a = client.post("/api/v1/patients", json=build_patient_payload("PAT-2005"), headers=ADMIN_HEADERS).json()
    patient_b = client.post("/api/v1/patients", json=build_patient_payload("PAT-2006"), headers=ADMIN_HEADERS).json()

    appointment_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_a["id"]),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = appointment_response.json()["id"]

    response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_b["id"],
            "appointment_id": appointment_id,
            "started_at": datetime.now(UTC).isoformat(),
        },
        headers=DOCTOR_HEADERS,
    )
    assert response.status_code == 409


def test_visit_rejects_cancelled_appointment(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2011"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    appointment_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = appointment_response.json()["id"]
    client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={"status": "cancelled"},
        headers=DOCTOR_HEADERS,
    )

    response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "started_at": datetime.now(UTC).isoformat(),
        },
        headers=DOCTOR_HEADERS,
    )
    assert response.status_code == 409


def test_visit_rejects_invalid_time_window(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2007"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    start = datetime.now(UTC)

    response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "started_at": start.isoformat(),
            "ended_at": (start - timedelta(hours=1)).isoformat(),
            "notes": "Invalid sample",
        },
        headers=DOCTOR_HEADERS,
    )
    assert response.status_code == 422


def test_delete_appointment_rejects_when_visit_exists(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2009"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    appointment_response = client.post(
        "/api/v1/appointments",
        json=build_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = appointment_response.json()["id"]
    client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "started_at": datetime.now(UTC).isoformat(),
        },
        headers=DOCTOR_HEADERS,
    )

    delete_response = client.delete(f"/api/v1/appointments/{appointment_id}", headers=ADMIN_HEADERS)
    assert delete_response.status_code == 409


def test_doctor_can_update_visit_notes(client) -> None:
    patient_response = client.post("/api/v1/patients", json=build_patient_payload("PAT-2012"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    visit_response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "started_at": datetime.now(UTC).isoformat(),
            "complaint": "Mild headache",
        },
        headers=DOCTOR_HEADERS,
    )
    visit_id = visit_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/visits/{visit_id}",
        json={"diagnosis_summary": "Tension headache", "notes": "Hydration and rest."},
        headers=DOCTOR_HEADERS,
    )
    assert update_response.status_code == 200
    assert update_response.json()["diagnosis_summary"] == "Tension headache"
