from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.rbac import Role


ADMIN_HEADERS = {"X-Demo-Role": "admin"}
RECEPTIONIST_HEADERS = {"X-Demo-Role": "receptionist"}
DOCTOR_ROLE_HEADERS = {"X-Demo-Role": "doctor"}


def _doctor_headers(user_id: str) -> dict[str, str]:
    return {"X-Demo-Role": "doctor", "X-Demo-User-Id": user_id}


def _create_patient_and_appointment(client, record_number: str) -> tuple[dict, dict]:
    patient_response = client.post(
        "/api/v1/patients",
        json={
            "record_number": record_number,
            "first_name": "Queue",
            "last_name": "Patient",
            "date_of_birth": "1994-07-10",
            "email": f"{record_number.lower()}@example.com",
            "phone": "+1 555 1301",
            "city": "Karachi",
            "notes": "Queue testing record.",
        },
        headers=ADMIN_HEADERS,
    )
    assert patient_response.status_code == 201
    patient = patient_response.json()

    appointment_response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient["id"],
            "scheduled_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "reason": "Queue check-in",
            "notes": "Queue test",
        },
        headers=DOCTOR_ROLE_HEADERS,
    )
    assert appointment_response.status_code == 201
    return patient, appointment_response.json()


def test_queue_check_in_assigns_predictable_order_by_doctor(client, create_user) -> None:
    doctor = create_user(
        email="doctor-queue-order@example.com",
        full_name="Dr. Queue Order",
        role=Role.DOCTOR,
        specialty="General Medicine",
        license_number="ND-QUEUE-0001",
    )

    _, appointment_one = _create_patient_and_appointment(client, "PAT-QUEUE-001")
    _, appointment_two = _create_patient_and_appointment(client, "PAT-QUEUE-002")

    first_check_in = client.post(
        f"/api/v1/appointments/{appointment_one['id']}/check-in",
        json={"assigned_doctor_id": str(doctor.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert first_check_in.status_code == 200
    assert first_check_in.json()["queue_number"] == 1

    second_check_in = client.post(
        f"/api/v1/appointments/{appointment_two['id']}/check-in",
        json={"assigned_doctor_id": str(doctor.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert second_check_in.status_code == 200
    assert second_check_in.json()["queue_number"] == 2

    list_response = client.get(
        f"/api/v1/queue/doctor/{doctor.id}?scheduled_date={appointment_one['scheduled_date']}",
        headers=RECEPTIONIST_HEADERS,
    )
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 2
    assert [item["queue_number"] for item in body["items"]] == [1, 2]


def test_queue_role_protection_and_doctor_identity_requirement(client, create_user, unsupported_role_headers) -> None:
    doctor = create_user(
        email="doctor-queue-auth@example.com",
        full_name="Dr. Queue Auth",
        role=Role.DOCTOR,
        specialty="Family Medicine",
        license_number="ND-QUEUE-0002",
    )
    _, appointment = _create_patient_and_appointment(client, "PAT-QUEUE-003")

    missing_auth = client.post(f"/api/v1/appointments/{appointment['id']}/check-in")
    assert missing_auth.status_code == 401

    unsupported_role = client.post(
        f"/api/v1/appointments/{appointment['id']}/check-in",
        headers=unsupported_role_headers,
    )
    assert unsupported_role.status_code == 403
    assert unsupported_role.json()["error"]["message"] == "Unsupported role"

    doctor_without_identity = client.get(
        f"/api/v1/queue/doctor/{doctor.id}?scheduled_date={appointment['scheduled_date']}",
        headers=DOCTOR_ROLE_HEADERS,
    )
    assert doctor_without_identity.status_code == 403
    assert doctor_without_identity.json()["error"]["message"] == "Doctor identity is required"


def test_queue_filtering_and_doctor_access_boundaries(client, create_user) -> None:
    doctor_a = create_user(
        email="doctor-queue-a@example.com",
        full_name="Dr. Queue A",
        role=Role.DOCTOR,
        specialty="Pediatrics",
        license_number="ND-QUEUE-0003",
    )
    doctor_b = create_user(
        email="doctor-queue-b@example.com",
        full_name="Dr. Queue B",
        role=Role.DOCTOR,
        specialty="Cardiology",
        license_number="ND-QUEUE-0004",
    )

    _, appointment_a = _create_patient_and_appointment(client, "PAT-QUEUE-004")
    _, appointment_b = _create_patient_and_appointment(client, "PAT-QUEUE-005")

    check_in_a = client.post(
        f"/api/v1/appointments/{appointment_a['id']}/check-in",
        json={"assigned_doctor_id": str(doctor_a.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    check_in_b = client.post(
        f"/api/v1/appointments/{appointment_b['id']}/check-in",
        json={"assigned_doctor_id": str(doctor_b.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert check_in_a.status_code == 200
    assert check_in_b.status_code == 200

    doctor_a_queue = client.get(
        f"/api/v1/queue/doctor/{doctor_a.id}?scheduled_date={appointment_a['scheduled_date']}",
        headers=ADMIN_HEADERS,
    )
    assert doctor_a_queue.status_code == 200
    assert doctor_a_queue.json()["total"] == 1
    assert doctor_a_queue.json()["items"][0]["assigned_doctor_id"] == str(doctor_a.id)

    doctor_a_self = client.get(
        f"/api/v1/queue/doctor/{doctor_a.id}?scheduled_date={appointment_a['scheduled_date']}",
        headers=_doctor_headers(str(doctor_a.id)),
    )
    assert doctor_a_self.status_code == 200
    assert doctor_a_self.json()["total"] == 1

    doctor_a_forbidden = client.get(
        f"/api/v1/queue/doctor/{doctor_b.id}?scheduled_date={appointment_a['scheduled_date']}",
        headers=_doctor_headers(str(doctor_a.id)),
    )
    assert doctor_a_forbidden.status_code == 403
    assert doctor_a_forbidden.json()["error"]["message"] == "Doctors can only view their own queue"


def test_queue_state_transitions_enforce_valid_flow(client, create_user) -> None:
    doctor = create_user(
        email="doctor-queue-flow@example.com",
        full_name="Dr. Queue Flow",
        role=Role.DOCTOR,
        specialty="Neurology",
        license_number="ND-QUEUE-0005",
    )
    _, appointment = _create_patient_and_appointment(client, "PAT-QUEUE-006")

    check_in = client.post(
        f"/api/v1/appointments/{appointment['id']}/check-in",
        json={"assigned_doctor_id": str(doctor.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert check_in.status_code == 200
    assert check_in.json()["queue_status"] == "waiting"

    call_response = client.post(
        f"/api/v1/queue/{appointment['id']}/call",
        headers=_doctor_headers(str(doctor.id)),
    )
    assert call_response.status_code == 200
    assert call_response.json()["queue_status"] == "in_progress"

    complete_response = client.post(
        f"/api/v1/queue/{appointment['id']}/complete",
        headers=_doctor_headers(str(doctor.id)),
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["queue_status"] == "completed"
    assert complete_response.json()["appointment_status"] == "completed"

    invalid_transition = client.post(
        f"/api/v1/queue/{appointment['id']}/skip",
        headers=_doctor_headers(str(doctor.id)),
    )
    assert invalid_transition.status_code == 409


def test_duplicate_check_in_is_rejected(client, create_user) -> None:
    doctor = create_user(
        email="doctor-queue-dup@example.com",
        full_name="Dr. Queue Duplicate",
        role=Role.DOCTOR,
        specialty="Orthopedics",
        license_number="ND-QUEUE-0006",
    )
    _, appointment = _create_patient_and_appointment(client, "PAT-QUEUE-007")

    first_check_in = client.post(
        f"/api/v1/appointments/{appointment['id']}/check-in",
        json={"assigned_doctor_id": str(doctor.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert first_check_in.status_code == 200

    duplicate_check_in = client.post(
        f"/api/v1/appointments/{appointment['id']}/check-in",
        json={"assigned_doctor_id": str(doctor.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert duplicate_check_in.status_code == 409
    assert duplicate_check_in.json()["error"]["message"] == "Appointment is already checked in"


def test_doctor_can_only_progress_assigned_queue(client, create_user) -> None:
    doctor_a = create_user(
        email="doctor-queue-own-a@example.com",
        full_name="Dr. Queue Own A",
        role=Role.DOCTOR,
        specialty="Dermatology",
        license_number="ND-QUEUE-0007",
    )
    doctor_b = create_user(
        email="doctor-queue-own-b@example.com",
        full_name="Dr. Queue Own B",
        role=Role.DOCTOR,
        specialty="ENT",
        license_number="ND-QUEUE-0008",
    )
    _, appointment = _create_patient_and_appointment(client, "PAT-QUEUE-008")

    check_in = client.post(
        f"/api/v1/appointments/{appointment['id']}/check-in",
        json={"assigned_doctor_id": str(doctor_a.id)},
        headers=RECEPTIONIST_HEADERS,
    )
    assert check_in.status_code == 200

    doctor_b_attempt = client.post(
        f"/api/v1/queue/{appointment['id']}/call",
        headers=_doctor_headers(str(doctor_b.id)),
    )
    assert doctor_b_attempt.status_code == 403
    assert doctor_b_attempt.json()["error"]["message"] == "Doctors can only manage their assigned queue"

    doctor_a_attempt = client.post(
        f"/api/v1/queue/{appointment['id']}/call",
        headers=_doctor_headers(str(doctor_a.id)),
    )
    assert doctor_a_attempt.status_code == 200
    assert doctor_a_attempt.json()["queue_status"] == "in_progress"
