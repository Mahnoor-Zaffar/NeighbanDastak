from __future__ import annotations

from datetime import date

def test_admin_can_create_patient(client, admin_headers, patient_payload_factory) -> None:
    response = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-1001"),
        headers=admin_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["record_number"] == "PAT-1001"
    assert body["first_name"] == "Amina"
    assert body["archived_at"] is None


def test_doctor_cannot_create_patient(client, doctor_headers, patient_payload_factory) -> None:
    response = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-1002"),
        headers=doctor_headers,
    )

    assert response.status_code == 403


def test_doctor_can_list_and_search_patients(
    client,
    admin_headers,
    doctor_headers,
    patient_payload_factory,
) -> None:
    client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-1003"),
        headers=admin_headers,
    )

    response = client.get("/api/v1/patients?q=Amina", headers=doctor_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["last_name"] == "Khan"


def test_admin_can_update_patient(client, admin_headers, patient_payload_factory) -> None:
    create_response = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-1004"),
        headers=admin_headers,
    )
    patient_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"city": "Lahore", "phone": "+1 555 0102"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Lahore"
    assert body["phone"] == "+1 555 0102"


def test_admin_can_archive_patient_and_list_archived(client, admin_headers, patient_payload_factory) -> None:
    create_response = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-1005"),
        headers=admin_headers,
    )
    patient_id = create_response.json()["id"]

    archive_response = client.delete(f"/api/v1/patients/{patient_id}", headers=admin_headers)
    assert archive_response.status_code == 200
    assert archive_response.json()["archived_at"] is not None

    default_list_response = client.get("/api/v1/patients", headers=admin_headers)
    assert default_list_response.status_code == 200
    assert default_list_response.json()["total"] == 0

    archived_list_response = client.get("/api/v1/patients?include_archived=true", headers=admin_headers)
    assert archived_list_response.status_code == 200
    assert archived_list_response.json()["total"] == 1


def test_patient_validation_rejects_future_birth_date(client, admin_headers, patient_payload_factory) -> None:
    payload = patient_payload_factory(record_number="PAT-1006")
    payload["date_of_birth"] = date.today().replace(year=date.today().year + 1).isoformat()

    response = client.post("/api/v1/patients", json=payload, headers=admin_headers)

    assert response.status_code == 422


def test_patient_requires_role_header(client) -> None:
    response = client.get("/api/v1/patients")

    assert response.status_code == 401


def test_get_patient_returns_detail(client, admin_headers, doctor_headers, patient_payload_factory) -> None:
    create_response = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-1001"),
        headers=admin_headers,
    )
    patient_id = create_response.json()["id"]

    response = client.get(f"/api/v1/patients/{patient_id}", headers=doctor_headers)

    assert response.status_code == 200
    assert response.json()["record_number"] == "PAT-1001"


def test_patient_record_number_must_be_unique(client, admin_headers, patient_payload_factory) -> None:
    first = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-UNIQ-001"),
        headers=admin_headers,
    )
    second = client.post(
        "/api/v1/patients",
        json=patient_payload_factory(record_number="PAT-UNIQ-001", email="second@example.com"),
        headers=admin_headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["message"] == "record_number already exists"


def test_patient_list_supports_limit_and_offset(client, admin_headers, doctor_headers, create_patient) -> None:
    create_patient(record_number="PAT-PAGE-001", headers=admin_headers, first_name="Ali", last_name="A")
    create_patient(record_number="PAT-PAGE-002", headers=admin_headers, first_name="Bilal", last_name="B")
    create_patient(record_number="PAT-PAGE-003", headers=admin_headers, first_name="C", last_name="C")

    response = client.get("/api/v1/patients?limit=2&offset=1", headers=doctor_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
