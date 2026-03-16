from __future__ import annotations


def test_patient_appointment_visit_lifecycle_flow(
    client,
    admin_headers,
    doctor_headers,
    create_patient,
    create_appointment,
    create_visit,
) -> None:
    patient_response = create_patient(record_number="PAT-I7001")
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    appointment_response = create_appointment(patient_id=patient_id)
    assert appointment_response.status_code == 201
    appointment_id = appointment_response.json()["id"]

    visit_response = create_visit(
        patient_id=patient_id,
        appointment_id=appointment_id,
        complaint="Follow-up fatigue",
        diagnosis_summary="Likely post-viral recovery",
    )
    assert visit_response.status_code == 201
    visit_id = visit_response.json()["id"]

    appointment_detail = client.get(f"/api/v1/appointments/{appointment_id}", headers=doctor_headers)
    assert appointment_detail.status_code == 200
    assert appointment_detail.json()["status"] == "completed"

    visit_detail = client.get(f"/api/v1/visits/{visit_id}", headers=doctor_headers)
    assert visit_detail.status_code == 200
    assert visit_detail.json()["appointment_id"] == appointment_id

    archive_response = client.delete(f"/api/v1/patients/{patient_id}", headers=admin_headers)
    assert archive_response.status_code == 200
    assert archive_response.json()["archived_at"] is not None

    after_archive_create = create_appointment(patient_id=patient_id)
    assert after_archive_create.status_code == 404
    assert after_archive_create.json()["error"]["message"] == "Patient not found"


def test_seed_data_drives_search_and_filtered_appointment_listing(
    client,
    doctor_headers,
    seed_clinic_data,
) -> None:
    seeded_patient = seed_clinic_data["patients"][0]
    seeded_visit = seed_clinic_data["visit"]

    search_response = client.get("/api/v1/patients?q=SEED-001", headers=doctor_headers)
    assert search_response.status_code == 200
    body = search_response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == seeded_patient["id"]

    completed_response = client.get("/api/v1/appointments?status=completed", headers=doctor_headers)
    assert completed_response.status_code == 200
    completed_body = completed_response.json()
    assert completed_body["total"] == 1
    assert completed_body["items"][0]["patient_id"] == seeded_patient["id"]

    visit_response = client.get(f"/api/v1/visits/{seeded_visit['id']}", headers=doctor_headers)
    assert visit_response.status_code == 200
    assert visit_response.json()["patient_id"] == seeded_patient["id"]
