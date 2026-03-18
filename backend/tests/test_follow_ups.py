from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.core.rbac import Role


ADMIN_HEADERS = {"X-Demo-Role": "admin"}
RECEPTIONIST_HEADERS = {"X-Demo-Role": "receptionist"}
DOCTOR_ROLE_HEADERS = {"X-Demo-Role": "doctor"}


def doctor_headers(doctor_id: str) -> dict[str, str]:
    return {"X-Demo-Role": "doctor", "X-Demo-User-Id": doctor_id}


def create_patient(client, record_number: str = "PAT-FUP-2001") -> dict:
    response = client.post(
        "/api/v1/patients",
        json={
            "record_number": record_number,
            "first_name": "Follow",
            "last_name": "Patient",
            "date_of_birth": "1990-03-21",
            "email": f"{record_number.lower()}@example.com",
            "phone": "+1 555 9911",
            "city": "Karachi",
            "notes": "Follow-up tests patient.",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def create_visit(client, patient_id: str) -> dict:
    response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "started_at": datetime.now(UTC).isoformat(),
            "complaint": "Headache and fatigue",
            "diagnosis_summary": "Migraine episode",
            "notes": "Follow-up advised in one week.",
        },
        headers=DOCTOR_ROLE_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def create_follow_up_payload(*, patient_id: str, visit_id: str, doctor_id: str, due_date: date) -> dict:
    return {
        "patient_id": patient_id,
        "visit_id": visit_id,
        "doctor_id": doctor_id,
        "due_date": due_date.isoformat(),
        "reason": "Reassess symptoms",
        "notes": "Review medication adherence and pain diary.",
    }


def test_doctor_can_create_follow_up(client, create_user) -> None:
    patient = create_patient(client, "PAT-FUP-2001")
    visit = create_visit(client, patient["id"])
    doctor = create_user(
        email="doctor-fup-create@example.com",
        full_name="Dr. Follow Create",
        role=Role.DOCTOR,
        specialty="Neurology",
        license_number="ND-FUP-0001",
    )

    response = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor.id),
            due_date=date.today() + timedelta(days=7),
        ),
        headers=doctor_headers(str(doctor.id)),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == patient["id"]
    assert body["visit_id"] == visit["id"]
    assert body["doctor_id"] == str(doctor.id)
    assert body["status"] == "pending"


def test_follow_up_status_transitions(client, create_user) -> None:
    patient = create_patient(client, "PAT-FUP-2002")
    visit = create_visit(client, patient["id"])
    doctor = create_user(
        email="doctor-fup-transitions@example.com",
        full_name="Dr. Follow Transition",
        role=Role.DOCTOR,
        specialty="General Medicine",
        license_number="ND-FUP-0002",
    )
    create_response = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor.id),
            due_date=date.today() + timedelta(days=5),
        ),
        headers=doctor_headers(str(doctor.id)),
    )
    assert create_response.status_code == 201
    follow_up_id = create_response.json()["id"]

    complete_response = client.post(
        f"/api/v1/follow-ups/{follow_up_id}/complete",
        headers=doctor_headers(str(doctor.id)),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"

    invalid_cancel = client.post(
        f"/api/v1/follow-ups/{follow_up_id}/cancel",
        headers=doctor_headers(str(doctor.id)),
    )
    assert invalid_cancel.status_code == 409


def test_follow_up_authorization_rules(client, create_user) -> None:
    patient = create_patient(client, "PAT-FUP-2003")
    visit = create_visit(client, patient["id"])
    doctor_a = create_user(
        email="doctor-fup-a@example.com",
        full_name="Dr. Follow A",
        role=Role.DOCTOR,
        specialty="Internal Medicine",
        license_number="ND-FUP-0003",
    )
    doctor_b = create_user(
        email="doctor-fup-b@example.com",
        full_name="Dr. Follow B",
        role=Role.DOCTOR,
        specialty="Family Medicine",
        license_number="ND-FUP-0004",
    )

    receptionist_create = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor_a.id),
            due_date=date.today() + timedelta(days=2),
        ),
        headers=RECEPTIONIST_HEADERS,
    )
    assert receptionist_create.status_code == 403

    create_response = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor_a.id),
            due_date=date.today() + timedelta(days=2),
        ),
        headers=doctor_headers(str(doctor_a.id)),
    )
    assert create_response.status_code == 201
    follow_up_id = create_response.json()["id"]

    missing_identity = client.get("/api/v1/follow-ups", headers=DOCTOR_ROLE_HEADERS)
    assert missing_identity.status_code == 403
    assert missing_identity.json()["error"]["message"] == "Doctor identity is required"

    other_doctor_update = client.put(
        f"/api/v1/follow-ups/{follow_up_id}",
        json={"notes": "Unauthorized update"},
        headers=doctor_headers(str(doctor_b.id)),
    )
    assert other_doctor_update.status_code == 403

    admin_can_view = client.get("/api/v1/follow-ups", headers=ADMIN_HEADERS)
    assert admin_can_view.status_code == 200
    assert admin_can_view.json()["total"] == 1


def test_doctor_lists_only_own_follow_ups(client, create_user) -> None:
    patient = create_patient(client, "PAT-FUP-2004")
    visit = create_visit(client, patient["id"])
    doctor_a = create_user(
        email="doctor-fup-list-a@example.com",
        full_name="Dr. Follow List A",
        role=Role.DOCTOR,
        specialty="Cardiology",
        license_number="ND-FUP-0005",
    )
    doctor_b = create_user(
        email="doctor-fup-list-b@example.com",
        full_name="Dr. Follow List B",
        role=Role.DOCTOR,
        specialty="Endocrinology",
        license_number="ND-FUP-0006",
    )

    response_a = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor_a.id),
            due_date=date.today() + timedelta(days=1),
        ),
        headers=doctor_headers(str(doctor_a.id)),
    )
    response_b = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor_b.id),
            due_date=date.today() + timedelta(days=3),
        ),
        headers=doctor_headers(str(doctor_b.id)),
    )
    assert response_a.status_code == 201
    assert response_b.status_code == 201

    list_a = client.get("/api/v1/follow-ups", headers=doctor_headers(str(doctor_a.id)))
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 1
    assert list_a.json()["items"][0]["doctor_id"] == str(doctor_a.id)

    patient_list_a = client.get(
        f"/api/v1/patients/{patient['id']}/follow-ups",
        headers=doctor_headers(str(doctor_a.id)),
    )
    assert patient_list_a.status_code == 200
    assert patient_list_a.json()["total"] == 1
    assert patient_list_a.json()["items"][0]["doctor_id"] == str(doctor_a.id)


def test_overdue_and_pending_filters(client, create_user) -> None:
    patient = create_patient(client, "PAT-FUP-2005")
    visit = create_visit(client, patient["id"])
    doctor = create_user(
        email="doctor-fup-filter@example.com",
        full_name="Dr. Follow Filter",
        role=Role.DOCTOR,
        specialty="Pulmonology",
        license_number="ND-FUP-0007",
    )

    overdue_create = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor.id),
            due_date=date.today() - timedelta(days=2),
        ),
        headers=doctor_headers(str(doctor.id)),
    )
    pending_create = client.post(
        "/api/v1/follow-ups",
        json=create_follow_up_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor.id),
            due_date=date.today() + timedelta(days=4),
        ),
        headers=doctor_headers(str(doctor.id)),
    )
    assert overdue_create.status_code == 201
    assert pending_create.status_code == 201

    overdue_list = client.get("/api/v1/follow-ups?status=overdue", headers=doctor_headers(str(doctor.id)))
    assert overdue_list.status_code == 200
    overdue_body = overdue_list.json()
    assert overdue_body["total"] == 1
    assert overdue_body["items"][0]["status"] == "overdue"

    pending_list = client.get("/api/v1/follow-ups?status=pending", headers=doctor_headers(str(doctor.id)))
    assert pending_list.status_code == 200
    pending_body = pending_list.json()
    assert pending_body["total"] == 1
    assert pending_body["items"][0]["status"] == "pending"
