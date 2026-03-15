from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from app.db.models.audit_log import AuditLog

ADMIN_HEADERS = {"X-Demo-Role": "admin"}
DOCTOR_HEADERS = {"X-Demo-Role": "doctor"}


def _patient_payload(record_number: str) -> dict[str, str]:
    return {
        "record_number": record_number,
        "first_name": "Nadia",
        "last_name": "Shah",
        "date_of_birth": "1990-03-03",
        "email": f"{record_number.lower()}@example.com",
        "phone": "+1 555 0303",
        "city": "Karachi",
        "notes": "Security test patient.",
    }


def _appointment_payload(patient_id: str) -> dict[str, str]:
    return {
        "patient_id": patient_id,
        "scheduled_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "reason": "Security review",
        "notes": "Audit logging check.",
    }


def test_patient_sensitive_actions_are_audited(client, db_session) -> None:
    create_response = client.post("/api/v1/patients", json=_patient_payload("PAT-5001"), headers=ADMIN_HEADERS)
    patient_id = create_response.json()["id"]

    client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"city": "Islamabad"},
        headers=ADMIN_HEADERS,
    )
    client.delete(f"/api/v1/patients/{patient_id}", headers=ADMIN_HEADERS)

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.resource_type == "patient",
                AuditLog.resource_id == UUID(patient_id),
            )
        )
    )
    actions = sorted(log.action for log in logs)
    assert "patient.create" in actions
    assert "patient.update" in actions
    assert "patient.archive" in actions


def test_appointment_status_change_is_audited(client, db_session) -> None:
    patient_response = client.post("/api/v1/patients", json=_patient_payload("PAT-5002"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    appointment_response = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(patient_id),
        headers=DOCTOR_HEADERS,
    )
    appointment_id = appointment_response.json()["id"]

    client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={"status": "completed"},
        headers=DOCTOR_HEADERS,
    )

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.resource_type == "appointment",
                AuditLog.resource_id == UUID(appointment_id),
            )
        )
    )
    actions = sorted(log.action for log in logs)
    assert "appointment.create" in actions
    assert "appointment.status_change" in actions


def test_doctor_cannot_reassign_appointment_patient(client) -> None:
    patient_a = client.post("/api/v1/patients", json=_patient_payload("PAT-5003"), headers=ADMIN_HEADERS).json()
    patient_b = client.post("/api/v1/patients", json=_patient_payload("PAT-5004"), headers=ADMIN_HEADERS).json()
    appointment = client.post(
        "/api/v1/appointments",
        json=_appointment_payload(patient_a["id"]),
        headers=DOCTOR_HEADERS,
    ).json()

    response = client.patch(
        f"/api/v1/appointments/{appointment['id']}",
        json={"patient_id": patient_b["id"]},
        headers=DOCTOR_HEADERS,
    )
    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "http_403"
    assert body["request_id"]


def test_validation_errors_use_standard_response_shape(client) -> None:
    response = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": "not-a-uuid",
            "scheduled_for": "2026-03-18T08:00",
        },
        headers=DOCTOR_HEADERS,
    )
    assert response.status_code == 422
    assert "X-Request-ID" in response.headers
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]
    assert body["request_id"]


def test_visit_update_is_audited(client, db_session) -> None:
    patient_response = client.post("/api/v1/patients", json=_patient_payload("PAT-5005"), headers=ADMIN_HEADERS)
    patient_id = patient_response.json()["id"]
    visit_response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "started_at": datetime.now(UTC).isoformat(),
            "complaint": "Follow up",
        },
        headers=DOCTOR_HEADERS,
    )
    visit_id = visit_response.json()["id"]

    client.patch(
        f"/api/v1/visits/{visit_id}",
        json={"notes": "Updated from security audit test."},
        headers=DOCTOR_HEADERS,
    )

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.resource_type == "visit",
                AuditLog.resource_id == UUID(visit_id),
            )
        )
    )
    actions = sorted(log.action for log in logs)
    assert "visit.create" in actions
    assert "visit.update" in actions
