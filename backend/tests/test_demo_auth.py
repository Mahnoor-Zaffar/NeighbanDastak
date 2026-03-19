from __future__ import annotations

from app.core.rbac import Role


def _doctor_headers(user_id: str) -> dict[str, str]:
    return {"X-Demo-Role": "doctor", "X-Demo-User-Id": user_id}


def test_demo_login_returns_doctor_profile_id_and_current_user(client, create_user) -> None:
    doctor = create_user(
        email="doctor-auth-demo@example.com",
        full_name="Dr. Demo Auth",
        role=Role.DOCTOR,
        specialty="Internal Medicine",
        license_number="ND-AUTH-0001",
    )

    login_response = client.post("/api/v1/auth/demo/login", json={"role": "doctor", "doctor_profile_id": str(doctor.id)})
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["role"] == "doctor"
    assert login_body["user_id"] == str(doctor.id)
    assert login_body["doctor_profile_id"] == str(doctor.id)
    assert login_body["full_name"] == "Dr. Demo Auth"

    current_user_response = client.get("/api/v1/auth/demo/current-user", headers=_doctor_headers(str(doctor.id)))
    assert current_user_response.status_code == 200
    current_user_body = current_user_response.json()
    assert current_user_body["role"] == "doctor"
    assert current_user_body["doctor_profile_id"] == str(doctor.id)


def test_demo_login_can_auto_select_first_active_doctor(client, create_user) -> None:
    create_user(
        email="doctor-zeta@example.com",
        full_name="Dr. Zeta",
        role=Role.DOCTOR,
        specialty="Neurology",
        license_number="ND-AUTH-0002",
    )
    doctor_alpha = create_user(
        email="doctor-alpha@example.com",
        full_name="Dr. Alpha",
        role=Role.DOCTOR,
        specialty="Cardiology",
        license_number="ND-AUTH-0003",
    )

    response = client.post("/api/v1/auth/demo/login", json={"role": "doctor"})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "doctor"
    assert body["doctor_profile_id"] == str(doctor_alpha.id)
    assert body["full_name"] == "Dr. Alpha"


def test_demo_auth_handles_missing_or_invalid_doctor_profile_gracefully(client, create_user) -> None:
    missing_profile_in_session = client.get("/api/v1/auth/demo/current-user", headers={"X-Demo-Role": "doctor"})
    assert missing_profile_in_session.status_code == 403
    assert missing_profile_in_session.json()["error"]["message"] == "Doctor profile is not linked to the current session"

    inactive_doctor = create_user(
        email="doctor-inactive-auth@example.com",
        full_name="Dr. Inactive",
        role=Role.DOCTOR,
        is_active=False,
        specialty="General Medicine",
        license_number="ND-AUTH-0004",
    )
    inactive_login = client.post(
        "/api/v1/auth/demo/login",
        json={"role": "doctor", "doctor_profile_id": str(inactive_doctor.id)},
    )
    assert inactive_login.status_code == 404
    assert inactive_login.json()["error"]["message"] == "Doctor profile not found"


def test_demo_doctor_profile_list_returns_active_doctors_only(client, create_user) -> None:
    active_doctor = create_user(
        email="doctor-list-active@example.com",
        full_name="Dr. Active Doctor",
        role=Role.DOCTOR,
        specialty="Pediatrics",
        license_number="ND-AUTH-0005",
    )
    create_user(
        email="doctor-list-inactive@example.com",
        full_name="Dr. Inactive Doctor",
        role=Role.DOCTOR,
        is_active=False,
        specialty="Dermatology",
        license_number="ND-AUTH-0006",
    )
    create_user(
        email="admin-list@example.com",
        full_name="Admin User",
        role=Role.ADMIN,
    )

    response = client.get("/api/v1/auth/demo/doctors")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(active_doctor.id)
    assert body["items"][0]["full_name"] == "Dr. Active Doctor"
