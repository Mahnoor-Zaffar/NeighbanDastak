from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from app.core.rbac import Role
from app.db.models.appointment import Appointment, AppointmentStatus
from app.db.models.visit import Visit

ADMIN_HEADERS = {"X-Demo-Role": "admin"}
DOCTOR_ROLE_HEADERS = {"X-Demo-Role": "doctor"}
RECEPTIONIST_HEADERS = {"X-Demo-Role": "receptionist"}


def _doctor_headers(user_id: str) -> dict[str, str]:
    return {"X-Demo-Role": "doctor", "X-Demo-User-Id": user_id}


def _datetime_on(day: date, *, hour: int) -> datetime:
    return datetime.combine(day, time(hour=hour, minute=0, second=0), tzinfo=UTC)


def _create_patient(client, record_number: str, first_name: str) -> dict:
    response = client.post(
        "/api/v1/patients",
        json={
            "record_number": record_number,
            "first_name": first_name,
            "last_name": "Analytics",
            "date_of_birth": "1992-07-11",
            "email": f"{record_number.lower()}@example.com",
            "phone": "+1 555 2101",
            "city": "Karachi",
            "notes": "Analytics test record.",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def test_analytics_authorization_and_doctor_identity_requirement(client, create_user, unsupported_role_headers) -> None:
    doctor = create_user(
        email="doctor-analytics-auth@example.com",
        full_name="Dr. Analytics Auth",
        role=Role.DOCTOR,
        specialty="Family Medicine",
        license_number="ND-AN-0001",
    )

    missing_auth = client.get("/api/v1/analytics/summary")
    assert missing_auth.status_code == 401

    unsupported_role = client.get("/api/v1/analytics/summary", headers=unsupported_role_headers)
    assert unsupported_role.status_code == 403
    assert unsupported_role.json()["error"]["message"] == "Unsupported role"

    doctor_missing_identity = client.get("/api/v1/analytics/summary", headers=DOCTOR_ROLE_HEADERS)
    assert doctor_missing_identity.status_code == 403
    assert doctor_missing_identity.json()["error"]["message"] == "Doctor identity is required"

    doctor_allowed = client.get("/api/v1/analytics/summary", headers=_doctor_headers(str(doctor.id)))
    assert doctor_allowed.status_code == 200

    receptionist_allowed = client.get("/api/v1/analytics/summary", headers=RECEPTIONIST_HEADERS)
    assert receptionist_allowed.status_code == 200


def test_analytics_aggregations_for_admin_and_doctor_scope(client, create_user, db_session) -> None:
    doctor_a = create_user(
        email="doctor-analytics-a@example.com",
        full_name="Dr. Analytics A",
        role=Role.DOCTOR,
        specialty="Internal Medicine",
        license_number="ND-AN-0002",
    )
    doctor_b = create_user(
        email="doctor-analytics-b@example.com",
        full_name="Dr. Analytics B",
        role=Role.DOCTOR,
        specialty="Cardiology",
        license_number="ND-AN-0003",
    )
    create_user(
        email="doctor-analytics-inactive@example.com",
        full_name="Dr. Analytics Inactive",
        role=Role.DOCTOR,
        is_active=False,
        specialty="ENT",
        license_number="ND-AN-0004",
    )

    patient_one = _create_patient(client, "PAT-AN-001", "Amina")
    patient_two = _create_patient(client, "PAT-AN-002", "Bilal")
    patient_three = _create_patient(client, "PAT-AN-003", "Sana")

    today = datetime.now(UTC).date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    within_week_not_today = week_start
    if within_week_not_today == today:
        within_week_not_today = week_start + timedelta(days=1)
    outside_week = week_start - timedelta(days=1)

    appointment_a_today = Appointment(
        patient_id=UUID(patient_one["id"]),
        scheduled_for=_datetime_on(today, hour=9),
        scheduled_date=today,
        status=AppointmentStatus.SCHEDULED,
        assigned_doctor_id=doctor_a.id,
        reason="Analytics appointment A1",
        notes="A1",
    )
    appointment_b_today = Appointment(
        patient_id=UUID(patient_two["id"]),
        scheduled_for=_datetime_on(today, hour=10),
        scheduled_date=today,
        status=AppointmentStatus.COMPLETED,
        assigned_doctor_id=doctor_a.id,
        reason="Analytics appointment A2",
        notes="A2",
    )
    appointment_c_today = Appointment(
        patient_id=UUID(patient_three["id"]),
        scheduled_for=_datetime_on(today, hour=11),
        scheduled_date=today,
        status=AppointmentStatus.COMPLETED,
        assigned_doctor_id=doctor_b.id,
        reason="Analytics appointment B1",
        notes="B1",
    )
    appointment_a_week = Appointment(
        patient_id=UUID(patient_one["id"]),
        scheduled_for=_datetime_on(within_week_not_today, hour=12),
        scheduled_date=within_week_not_today,
        status=AppointmentStatus.NO_SHOW,
        assigned_doctor_id=doctor_a.id,
        reason="Analytics appointment A3",
        notes="A3",
    )
    appointment_outside_week = Appointment(
        patient_id=UUID(patient_two["id"]),
        scheduled_for=_datetime_on(outside_week, hour=14),
        scheduled_date=outside_week,
        status=AppointmentStatus.SCHEDULED,
        assigned_doctor_id=doctor_b.id,
        reason="Analytics appointment B2",
        notes="B2",
    )
    db_session.add_all(
        [
            appointment_a_today,
            appointment_b_today,
            appointment_c_today,
            appointment_a_week,
            appointment_outside_week,
        ]
    )
    db_session.commit()
    db_session.refresh(appointment_b_today)
    db_session.refresh(appointment_c_today)

    db_session.add_all(
        [
            Visit(
                patient_id=UUID(patient_two["id"]),
                appointment_id=appointment_b_today.id,
                started_at=_datetime_on(today, hour=10),
                ended_at=_datetime_on(today, hour=11),
                complaint="Analytics follow-up",
                diagnosis_summary="Stable condition",
                notes="Visit for analytics metrics A2.",
            ),
            Visit(
                patient_id=UUID(patient_three["id"]),
                appointment_id=appointment_c_today.id,
                started_at=_datetime_on(today, hour=11),
                ended_at=_datetime_on(today, hour=12),
                complaint="Analytics follow-up",
                diagnosis_summary="Stable condition",
                notes="Visit for analytics metrics B1.",
            ),
        ]
    )
    db_session.commit()

    admin_summary_response = client.get("/api/v1/analytics/summary", headers=ADMIN_HEADERS)
    assert admin_summary_response.status_code == 200
    admin_summary = admin_summary_response.json()
    assert admin_summary["total_patients"] == 3
    assert admin_summary["active_doctors"] == 2
    assert admin_summary["appointments_today"] == 3
    assert admin_summary["completed_visits_today"] == 2
    assert admin_summary["appointments_this_week"] == 4

    doctor_summary_response = client.get("/api/v1/analytics/summary", headers=_doctor_headers(str(doctor_a.id)))
    assert doctor_summary_response.status_code == 200
    doctor_summary = doctor_summary_response.json()
    assert doctor_summary["scope"] == "doctor"
    assert doctor_summary["total_patients"] == 2
    assert doctor_summary["active_doctors"] == 1
    assert doctor_summary["appointments_today"] == 2
    assert doctor_summary["completed_visits_today"] == 1
    assert doctor_summary["appointments_this_week"] == 3

    breakdown_response = client.get(
        f"/api/v1/analytics/appointment-status-breakdown?starts_on={week_start.isoformat()}&ends_on={week_end.isoformat()}",
        headers=_doctor_headers(str(doctor_a.id)),
    )
    assert breakdown_response.status_code == 200
    breakdown_by_status = {
        item["status"]: item["count"] for item in breakdown_response.json()["items"]
    }
    assert breakdown_by_status["scheduled"] == 1
    assert breakdown_by_status["completed"] == 1
    assert breakdown_by_status["no_show"] == 1
    assert breakdown_by_status["cancelled"] == 0

    workload_response = client.get(
        f"/api/v1/analytics/doctor-workload?starts_on={week_start.isoformat()}&ends_on={week_end.isoformat()}",
        headers=ADMIN_HEADERS,
    )
    assert workload_response.status_code == 200
    workload_items = workload_response.json()["items"]
    workload_map = {item["doctor_id"]: item["appointments_count"] for item in workload_items}
    assert workload_map[str(doctor_a.id)] == 3
    assert workload_map[str(doctor_b.id)] == 1

    doctor_workload_response = client.get(
        f"/api/v1/analytics/doctor-workload?starts_on={week_start.isoformat()}&ends_on={week_end.isoformat()}",
        headers=_doctor_headers(str(doctor_a.id)),
    )
    assert doctor_workload_response.status_code == 200
    doctor_workload_items = doctor_workload_response.json()["items"]
    assert len(doctor_workload_items) == 1
    assert doctor_workload_items[0]["doctor_id"] == str(doctor_a.id)
    assert doctor_workload_items[0]["appointments_count"] == 3

    by_day_response = client.get(
        "/api/v1/analytics/appointments-by-day?days=3",
        headers=ADMIN_HEADERS,
    )
    assert by_day_response.status_code == 200
    by_day_body = by_day_response.json()
    assert by_day_body["total"] == 3
    assert len(by_day_body["items"]) == 3
    assert [item["day"] for item in by_day_body["items"]] == sorted(item["day"] for item in by_day_body["items"])


def test_analytics_empty_data_behavior(client) -> None:
    summary_response = client.get("/api/v1/analytics/summary", headers=ADMIN_HEADERS)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_patients"] == 0
    assert summary["active_doctors"] == 0
    assert summary["appointments_today"] == 0
    assert summary["completed_visits_today"] == 0
    assert summary["appointments_this_week"] == 0

    by_day_response = client.get("/api/v1/analytics/appointments-by-day?days=5", headers=ADMIN_HEADERS)
    assert by_day_response.status_code == 200
    by_day = by_day_response.json()
    assert by_day["total"] == 5
    assert len(by_day["items"]) == 5
    assert all(item["appointments_count"] == 0 for item in by_day["items"])

    workload_response = client.get("/api/v1/analytics/doctor-workload", headers=ADMIN_HEADERS)
    assert workload_response.status_code == 200
    workload = workload_response.json()
    assert workload["total"] == 0
    assert workload["items"] == []

    breakdown_response = client.get("/api/v1/analytics/appointment-status-breakdown", headers=ADMIN_HEADERS)
    assert breakdown_response.status_code == 200
    breakdown = breakdown_response.json()
    assert breakdown["total"] == 4
    assert all(item["count"] == 0 for item in breakdown["items"])


def test_analytics_doctor_filter_for_admin_and_doctor_restriction(client, create_user, db_session) -> None:
    doctor_a = create_user(
        email="doctor-analytics-filter-a@example.com",
        full_name="Dr. Analytics Filter A",
        role=Role.DOCTOR,
        specialty="Internal Medicine",
        license_number="ND-AN-0101",
    )
    doctor_b = create_user(
        email="doctor-analytics-filter-b@example.com",
        full_name="Dr. Analytics Filter B",
        role=Role.DOCTOR,
        specialty="Cardiology",
        license_number="ND-AN-0102",
    )

    patient_one = _create_patient(client, "PAT-AN-F01", "Hina")
    patient_two = _create_patient(client, "PAT-AN-F02", "Usman")

    today = datetime.now(UTC).date()
    db_session.add_all(
        [
            Appointment(
                patient_id=UUID(patient_one["id"]),
                scheduled_for=_datetime_on(today, hour=9),
                scheduled_date=today,
                status=AppointmentStatus.SCHEDULED,
                assigned_doctor_id=doctor_a.id,
                reason="Filter appointment A",
                notes="A",
            ),
            Appointment(
                patient_id=UUID(patient_two["id"]),
                scheduled_for=_datetime_on(today, hour=10),
                scheduled_date=today,
                status=AppointmentStatus.COMPLETED,
                assigned_doctor_id=doctor_b.id,
                reason="Filter appointment B",
                notes="B",
            ),
        ]
    )
    db_session.commit()

    admin_filtered_summary = client.get(f"/api/v1/analytics/summary?doctor_id={doctor_a.id}", headers=ADMIN_HEADERS)
    assert admin_filtered_summary.status_code == 200
    filtered_body = admin_filtered_summary.json()
    assert filtered_body["scope"] == "doctor"
    assert filtered_body["active_doctors"] == 1
    assert filtered_body["appointments_today"] == 1

    doctor_forbidden = client.get(
        f"/api/v1/analytics/summary?doctor_id={doctor_b.id}",
        headers=_doctor_headers(str(doctor_a.id)),
    )
    assert doctor_forbidden.status_code == 403
    assert doctor_forbidden.json()["error"]["message"] == "Doctor cannot access another doctor's analytics"

    missing_doctor = client.get(
        "/api/v1/analytics/summary?doctor_id=00000000-0000-0000-0000-000000000001",
        headers=ADMIN_HEADERS,
    )
    assert missing_doctor.status_code == 404
    assert missing_doctor.json()["error"]["message"] == "Doctor not found"
