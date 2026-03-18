from __future__ import annotations

from datetime import UTC, datetime

from app.core.rbac import Role


ADMIN_HEADERS = {"X-Demo-Role": "admin"}
DOCTOR_HEADERS = {"X-Demo-Role": "doctor"}


def build_patient_payload(record_number: str = "PAT-RX-2001") -> dict[str, str]:
    return {
        "record_number": record_number,
        "first_name": "Areeba",
        "last_name": "Shah",
        "date_of_birth": "1992-03-18",
        "email": f"{record_number.lower()}@example.com",
        "phone": "+1 555 9901",
        "city": "Karachi",
        "notes": "Prescription tests patient.",
    }


def create_patient(client, record_number: str) -> dict:
    response = client.post("/api/v1/patients", json=build_patient_payload(record_number), headers=ADMIN_HEADERS)
    assert response.status_code == 201
    return response.json()


def create_visit(client, patient_id: str) -> dict:
    response = client.post(
        "/api/v1/visits",
        json={
            "patient_id": patient_id,
            "started_at": datetime.now(UTC).isoformat(),
            "complaint": "Fever with sore throat",
            "diagnosis_summary": "Acute pharyngitis",
        },
        headers=DOCTOR_HEADERS,
    )
    assert response.status_code == 201
    return response.json()


def build_prescription_payload(*, patient_id: str, visit_id: str, doctor_id: str, with_items: bool = True) -> dict:
    payload = {
        "patient_id": patient_id,
        "visit_id": visit_id,
        "doctor_id": doctor_id,
        "diagnosis_summary": "Upper respiratory tract infection",
        "notes": "Take medications after meals.",
        "items": [
            {
                "medicine_name": "Amoxicillin",
                "dosage": "500mg",
                "frequency": "Every 8 hours",
                "duration": "5 days",
                "instructions": "Complete full course.",
            },
            {
                "medicine_name": "Paracetamol",
                "dosage": "650mg",
                "frequency": "Every 6 hours as needed",
                "duration": "3 days",
                "instructions": "Only if fever exceeds 100F.",
            },
        ],
    }
    if not with_items:
        payload["items"] = []
    return payload


def test_doctor_can_create_prescription(client, create_user) -> None:
    patient = create_patient(client, "PAT-RX-2001")
    visit = create_visit(client, patient["id"])
    doctor_user = create_user(
        email="doctor-rx-create@example.com",
        full_name="Dr. Test Create",
        role=Role.DOCTOR,
        specialty="Internal Medicine",
        license_number="ND-RX-0001",
    )

    response = client.post(
        "/api/v1/prescriptions",
        json=build_prescription_payload(patient_id=patient["id"], visit_id=visit["id"], doctor_id=str(doctor_user.id)),
        headers=DOCTOR_HEADERS,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == patient["id"]
    assert body["visit_id"] == visit["id"]
    assert body["doctor_id"] == str(doctor_user.id)
    assert len(body["items"]) == 2
    assert body["items"][0]["medicine_name"] == "Amoxicillin"


def test_prescription_requires_role_header(client) -> None:
    response = client.get("/api/v1/prescriptions/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 401
    assert "X-Request-ID" in response.headers
    body = response.json()
    assert body["error"]["code"] == "http_401"
    assert "X-Demo-Role" in body["error"]["message"]


def test_receptionist_cannot_create_prescription(client, receptionist_headers, create_user) -> None:
    patient = create_patient(client, "PAT-RX-2002")
    visit = create_visit(client, patient["id"])
    doctor_user = create_user(
        email="doctor-rx-receptionist@example.com",
        full_name="Dr. Test Reception",
        role=Role.DOCTOR,
        specialty="Family Medicine",
        license_number="ND-RX-0002",
    )

    response = client.post(
        "/api/v1/prescriptions",
        json=build_prescription_payload(patient_id=patient["id"], visit_id=visit["id"], doctor_id=str(doctor_user.id)),
        headers=receptionist_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "You do not have permission to perform this action"


def test_fetch_patient_and_visit_prescriptions(client, create_user) -> None:
    patient = create_patient(client, "PAT-RX-2003")
    visit = create_visit(client, patient["id"])
    doctor_user = create_user(
        email="doctor-rx-list@example.com",
        full_name="Dr. Test List",
        role=Role.DOCTOR,
        specialty="General Medicine",
        license_number="ND-RX-0003",
    )
    create_payload = build_prescription_payload(
        patient_id=patient["id"],
        visit_id=visit["id"],
        doctor_id=str(doctor_user.id),
    )
    create_response = client.post("/api/v1/prescriptions", json=create_payload, headers=ADMIN_HEADERS)
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    patient_list_response = client.get(f"/api/v1/patients/{patient['id']}/prescriptions", headers=DOCTOR_HEADERS)
    assert patient_list_response.status_code == 200
    assert patient_list_response.json()["total"] == 1
    assert patient_list_response.json()["items"][0]["id"] == prescription_id

    visit_list_response = client.get(f"/api/v1/visits/{visit['id']}/prescriptions", headers=DOCTOR_HEADERS)
    assert visit_list_response.status_code == 200
    assert visit_list_response.json()["total"] == 1
    assert visit_list_response.json()["items"][0]["id"] == prescription_id


def test_update_prescription_replaces_items(client, create_user) -> None:
    patient = create_patient(client, "PAT-RX-2004")
    visit = create_visit(client, patient["id"])
    doctor_user = create_user(
        email="doctor-rx-update@example.com",
        full_name="Dr. Test Update",
        role=Role.DOCTOR,
        specialty="General Medicine",
        license_number="ND-RX-0004",
    )
    create_response = client.post(
        "/api/v1/prescriptions",
        json=build_prescription_payload(patient_id=patient["id"], visit_id=visit["id"], doctor_id=str(doctor_user.id)),
        headers=DOCTOR_HEADERS,
    )
    assert create_response.status_code == 201
    prescription_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/prescriptions/{prescription_id}",
        json={
            "diagnosis_summary": "Bacterial sinusitis",
            "notes": "Steam inhalation advised.",
            "items": [
                {
                    "medicine_name": "Azithromycin",
                    "dosage": "500mg",
                    "frequency": "Once daily",
                    "duration": "3 days",
                    "instructions": "Take one hour before meals.",
                }
            ],
        },
        headers=DOCTOR_HEADERS,
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["diagnosis_summary"] == "Bacterial sinusitis"
    assert len(body["items"]) == 1
    assert body["items"][0]["medicine_name"] == "Azithromycin"


def test_prescription_creation_rejects_non_doctor_user_as_author(client, create_user) -> None:
    patient = create_patient(client, "PAT-RX-2005")
    visit = create_visit(client, patient["id"])
    admin_user = create_user(
        email="admin-rx-author@example.com",
        full_name="Admin Author",
        role=Role.ADMIN,
    )

    response = client.post(
        "/api/v1/prescriptions",
        json=build_prescription_payload(patient_id=patient["id"], visit_id=visit["id"], doctor_id=str(admin_user.id)),
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Doctor not found"


def test_prescription_validation_failures(client, create_user) -> None:
    patient = create_patient(client, "PAT-RX-2006")
    visit = create_visit(client, patient["id"])
    doctor_user = create_user(
        email="doctor-rx-validate@example.com",
        full_name="Dr. Test Validate",
        role=Role.DOCTOR,
        specialty="General Medicine",
        license_number="ND-RX-0005",
    )

    empty_items_response = client.post(
        "/api/v1/prescriptions",
        json=build_prescription_payload(
            patient_id=patient["id"],
            visit_id=visit["id"],
            doctor_id=str(doctor_user.id),
            with_items=False,
        ),
        headers=DOCTOR_HEADERS,
    )
    assert empty_items_response.status_code == 422
    assert empty_items_response.json()["error"]["code"] == "validation_error"

    missing_medicine_response = client.post(
        "/api/v1/prescriptions",
        json={
            "patient_id": patient["id"],
            "visit_id": visit["id"],
            "doctor_id": str(doctor_user.id),
            "diagnosis_summary": "Sample diagnosis",
            "items": [
                {
                    "medicine_name": "",
                    "dosage": "10mg",
                    "frequency": "Once daily",
                    "duration": "7 days",
                }
            ],
        },
        headers=DOCTOR_HEADERS,
    )
    assert missing_medicine_response.status_code == 422
    assert missing_medicine_response.json()["error"]["code"] == "validation_error"


def test_prescription_rejects_visit_patient_mismatch(client, create_user) -> None:
    patient_one = create_patient(client, "PAT-RX-2007")
    patient_two = create_patient(client, "PAT-RX-2008")
    visit_for_patient_one = create_visit(client, patient_one["id"])
    doctor_user = create_user(
        email="doctor-rx-mismatch@example.com",
        full_name="Dr. Test Mismatch",
        role=Role.DOCTOR,
        specialty="General Medicine",
        license_number="ND-RX-0006",
    )

    response = client.post(
        "/api/v1/prescriptions",
        json=build_prescription_payload(
            patient_id=patient_two["id"],
            visit_id=visit_for_patient_one["id"],
            doctor_id=str(doctor_user.id),
        ),
        headers=DOCTOR_HEADERS,
    )

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "visit does not belong to the provided patient"
