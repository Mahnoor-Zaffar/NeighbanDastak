from __future__ import annotations

from datetime import date


ADMIN_HEADERS = {"X-Demo-Role": "admin"}
DOCTOR_HEADERS = {"X-Demo-Role": "doctor"}


def build_patient_payload() -> dict[str, str]:
    return {
        "record_number": "PAT-1001",
        "first_name": "Amina",
        "last_name": "Khan",
        "date_of_birth": "1993-04-18",
        "email": "amina@example.com",
        "phone": "+1 555 0101",
        "city": "Karachi",
        "notes": "Demo patient record.",
    }


def test_admin_can_create_patient(client) -> None:
    response = client.post("/api/v1/patients", json=build_patient_payload(), headers=ADMIN_HEADERS)

    assert response.status_code == 201
    body = response.json()
    assert body["record_number"] == "PAT-1001"
    assert body["first_name"] == "Amina"
    assert body["archived_at"] is None


def test_doctor_cannot_create_patient(client) -> None:
    response = client.post("/api/v1/patients", json=build_patient_payload(), headers=DOCTOR_HEADERS)

    assert response.status_code == 403


def test_doctor_can_list_and_search_patients(client) -> None:
    client.post("/api/v1/patients", json=build_patient_payload(), headers=ADMIN_HEADERS)

    response = client.get("/api/v1/patients?q=Amina", headers=DOCTOR_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["last_name"] == "Khan"


def test_admin_can_update_patient(client) -> None:
    create_response = client.post("/api/v1/patients", json=build_patient_payload(), headers=ADMIN_HEADERS)
    patient_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"city": "Lahore", "phone": "+1 555 0102"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Lahore"
    assert body["phone"] == "+1 555 0102"


def test_admin_can_archive_patient_and_list_archived(client) -> None:
    create_response = client.post("/api/v1/patients", json=build_patient_payload(), headers=ADMIN_HEADERS)
    patient_id = create_response.json()["id"]

    archive_response = client.delete(f"/api/v1/patients/{patient_id}", headers=ADMIN_HEADERS)
    assert archive_response.status_code == 200
    assert archive_response.json()["archived_at"] is not None

    default_list_response = client.get("/api/v1/patients", headers=ADMIN_HEADERS)
    assert default_list_response.status_code == 200
    assert default_list_response.json()["total"] == 0

    archived_list_response = client.get("/api/v1/patients?include_archived=true", headers=ADMIN_HEADERS)
    assert archived_list_response.status_code == 200
    assert archived_list_response.json()["total"] == 1


def test_patient_validation_rejects_future_birth_date(client) -> None:
    payload = build_patient_payload()
    payload["date_of_birth"] = date.today().replace(year=date.today().year + 1).isoformat()

    response = client.post("/api/v1/patients", json=payload, headers=ADMIN_HEADERS)

    assert response.status_code == 422


def test_patient_requires_role_header(client) -> None:
    response = client.get("/api/v1/patients")

    assert response.status_code == 401


def test_get_patient_returns_detail(client) -> None:
    create_response = client.post("/api/v1/patients", json=build_patient_payload(), headers=ADMIN_HEADERS)
    patient_id = create_response.json()["id"]

    response = client.get(f"/api/v1/patients/{patient_id}", headers=DOCTOR_HEADERS)

    assert response.status_code == 200
    assert response.json()["record_number"] == "PAT-1001"
