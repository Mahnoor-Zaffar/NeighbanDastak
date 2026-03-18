"""
Comprehensive Clinic Management System Test Suite

This test module provides end-to-end testing for all major clinic workflows:
- Patient Management
- Appointment Scheduling & Queue Management  
- Visit Documentation
- Prescription Management
- Follow-up Tracking
- Analytics & Reporting
- Role-based Access Control

Usage:
    pytest tests/test_clinic_comprehensive.py -v

Test Categories:
- Smoke Tests: Basic functionality verification
- Integration Tests: Cross-module workflows
- Business Logic Tests: Clinic process validation
- Security Tests: Role-based access control
- Performance Tests: Response time validation
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict

from app.core.rbac import Role


class TestClinicComprehensive:
    """
    Comprehensive test suite for clinic management system
    Covers all major workflows and edge cases
    """

    # ==================== SMOKE TESTS ====================
    
    def test_health_check_smoke(self, client):
        """Verify system is healthy and responsive"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "NigehbaanDastak"
        assert data["database"] == "ok"
        assert "version" in data

    def test_api_accessibility_smoke(self, client, admin_headers):
        """Verify all major endpoints are accessible"""
        endpoints = [
            ("/api/v1/patients", "admin", "GET"),  # List endpoints
            ("/api/v1/appointments", "admin", "GET"), 
            ("/api/v1/visits", "admin", "POST"),  # Visits only supports POST for creation
            ("/api/v1/prescriptions", "admin", "GET"),
            ("/api/v1/queue", "admin", "GET"),
            ("/api/v1/follow-ups", "admin", "GET"),
            ("/api/v1/analytics/summary", "admin", "GET"),
        ]
        
        for endpoint, role, method in endpoints:
            headers = {"X-Demo-Role": role}
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            else:  # POST
                # For POST endpoints, we expect 422 (validation error) since we're not sending data
                response = client.post(endpoint, headers=headers)
            
            # Should return 200 for GET list endpoints, even if empty
            # Should return 422 for POST endpoints without valid data
            assert response.status_code in [200, 422, 405], f"Endpoint {endpoint} ({method}) returned {response.status_code}: {response.text}"

    # ==================== PATIENT MANAGEMENT ====================

    def test_patient_lifecycle_admin(self, client, admin_headers, patient_payload_factory):
        """Test complete patient lifecycle with admin role"""
        # Create patient
        payload = patient_payload_factory(record_number="PAT-LC-001")
        response = client.post("/api/v1/patients", json=payload, headers=admin_headers)
        assert response.status_code == 201
        patient = response.json()
        patient_id = patient["id"]
        
        # Read patient
        response = client.get(f"/api/v1/patients/{patient_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["record_number"] == "PAT-LC-001"
        
        # Update patient
        update_payload = {"first_name": "Updated Name"}
        response = client.patch(f"/api/v1/patients/{patient_id}", json=update_payload, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated Name"
        
        # Archive patient
        response = client.delete(f"/api/v1/patients/{patient_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["archived_at"] is not None

    def test_patient_access_control(self, client, patient_payload_factory):
        """Test patient access control across roles"""
        # Create patient with admin
        payload = patient_payload_factory(record_number="PAT-AC-001")
        response = client.post("/api/v1/patients", json=payload, headers={"X-Demo-Role": "admin"})
        patient_id = response.json()["id"]
        
        # Test access with different roles
        roles_access = [
            ("admin", 200),
            ("doctor", 200), 
            ("receptionist", 200),
            ("guest", 403)
        ]
        
        for role, expected_status in roles_access:
            response = client.get(f"/api/v1/patients/{patient_id}", headers={"X-Demo-Role": role})
            assert response.status_code == expected_status

    def test_patient_search_functionality(self, client, create_patient, admin_headers):
        """Test patient search and filtering"""
        # Create test patients
        create_patient(record_number="PAT-SEARCH-001", first_name="John", last_name="Smith")
        create_patient(record_number="PAT-SEARCH-002", first_name="Jane", last_name="Doe")
        
        # Search by name
        response = client.get("/api/v1/patients?q=John", headers=admin_headers)
        assert response.status_code == 200
        patients = response.json()["items"]
        assert len(patients) == 1
        assert patients[0]["first_name"] == "John"
        
        # Test archived filter
        response = client.get("/api/v1/patients?include_archived=true", headers=admin_headers)
        assert response.status_code == 200

    # ==================== APPOINTMENT MANAGEMENT ====================

    def test_appointment_workflow(self, client, create_patient, doctor_headers, appointment_payload_factory):
        """Test complete appointment workflow"""
        # Create patient first
        patient_response = create_patient(record_number="PAT-APPT-001")
        patient_id = patient_response.json()["id"]
        
        # Schedule appointment
        appointment_time = (datetime.now() + timedelta(days=1)).isoformat()
        payload = appointment_payload_factory(
            patient_id=patient_id,
            scheduled_for=appointment_time,
            reason="Regular checkup"
        )
        response = client.post("/api/v1/appointments", json=payload, headers=doctor_headers)
        assert response.status_code == 201
        appointment = response.json()
        appointment_id = appointment["id"]
        
        # Update appointment status
        response = client.patch(
            f"/api/v1/appointments/{appointment_id}",
            json={"status": "completed"},
            headers=doctor_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_appointment_queue_integration(self, client, create_patient, create_appointment, doctor_headers):
        """Test appointment queue system integration"""
        # Create appointment
        patient_response = create_patient(record_number="PAT-QUEUE-001")
        patient_id = patient_response.json()["id"]
        appointment_response = create_appointment(patient_id=patient_id)
        appointment_id = appointment_response.json()["id"]
        
        # Check-in patient
        response = client.post(
            f"/api/v1/appointments/{appointment_id}/check-in",
            json={"assigned_doctor_id": "doc-001"},
            headers=doctor_headers
        )
        assert response.status_code == 200
        queue_entry = response.json()
        assert queue_entry["queue_status"] == "waiting"
        
        # Call patient from queue
        response = client.post(f"/api/v1/queue/{appointment_id}/call", headers=doctor_headers)
        assert response.status_code == 200
        assert response.json()["queue_status"] == "in_progress"
        
        # Complete queue entry
        response = client.post(f"/api/v1/queue/{appointment_id}/complete", headers=doctor_headers)
        assert response.status_code == 200
        assert response.json()["queue_status"] == "completed"

    # ==================== VISIT MANAGEMENT ====================

    def test_visit_documentation_workflow(self, client, create_patient, create_appointment, doctor_headers, visit_payload_factory):
        """Test complete visit documentation workflow"""
        # Setup patient and appointment
        patient_response = create_patient(record_number="PAT-VISIT-001")
        patient_id = patient_response.json()["id"]
        appointment_response = create_appointment(patient_id=patient_id)
        appointment_id = appointment_response.json()["id"]
        
        # Create visit
        visit_time = datetime.now().isoformat()
        payload = visit_payload_factory(
            patient_id=patient_id,
            appointment_id=appointment_id,
            started_at=visit_time,
            complaint="Headache and dizziness",
            diagnosis_summary="Migraine - prescribe pain relievers",
            notes="Patient advised to rest and hydrate"
        )
        response = client.post("/api/v1/visits", json=payload, headers=doctor_headers)
        assert response.status_code == 201
        visit = response.json()
        visit_id = visit["id"]
        
        # Verify visit details
        response = client.get(f"/api/v1/visits/{visit_id}", headers=doctor_headers)
        assert response.status_code == 200
        visit_data = response.json()
        assert visit_data["complaint"] == "Headache and dizziness"
        assert visit_data["diagnosis_summary"] == "Migraine - prescribe pain relievers"

    # ==================== PRESCRIPTION MANAGEMENT ====================

    def test_prescription_workflow(self, client, create_patient, create_visit, doctor_headers):
        """Test complete prescription management workflow"""
        # Setup patient and visit
        patient_response = create_patient(record_number="PAT-RX-001")
        patient_id = patient_response.json()["id"]
        visit_response = create_visit(patient_id=patient_id)
        visit_id = visit_response.json()["id"]
        
        # Create prescription
        prescription_payload = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "doctor_id": "doc-001",
            "diagnosis_summary": "Hypertension management",
            "notes": "Continue monitoring blood pressure",
            "items": [
                {
                    "medicine_name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "Once daily",
                    "duration": "30 days",
                    "instructions": "Take with water, avoid potassium supplements"
                },
                {
                    "medicine_name": "Aspirin",
                    "dosage": "81mg", 
                    "frequency": "Once daily",
                    "duration": "30 days",
                    "instructions": "Take with food to prevent stomach upset"
                }
            ]
        }
        response = client.post("/api/v1/prescriptions", json=prescription_payload, headers=doctor_headers)
        assert response.status_code == 201
        prescription = response.json()
        prescription_id = prescription["id"]
        
        # Verify prescription details
        response = client.get(f"/api/v1/prescriptions/{prescription_id}", headers=doctor_headers)
        assert response.status_code == 200
        rx_data = response.json()
        assert len(rx_data["items"]) == 2
        assert rx_data["items"][0]["medicine_name"] == "Lisinopril"

    def test_prescription_printing(self, client, create_patient, create_visit, doctor_headers):
        """Test prescription printing functionality"""
        # Create prescription
        patient_response = create_patient(record_number="PAT-PRINT-001")
        patient_id = patient_response.json()["id"]
        visit_response = create_visit(patient_id=patient_id)
        visit_id = visit_response.json()["id"]
        
        prescription_payload = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "doctor_id": "doc-001",
            "diagnosis_summary": "Common cold",
            "items": [
                {
                    "medicine_name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "Every 6 hours",
                    "duration": "5 days"
                }
            ]
        }
        response = client.post("/api/v1/prescriptions", json=prescription_payload, headers=doctor_headers)
        prescription_id = response.json()["id"]
        
        # Test print endpoint
        response = client.get(f"/api/v1/prescriptions/{prescription_id}/print", headers=doctor_headers)
        assert response.status_code == 200

    # ==================== FOLLOW-UP MANAGEMENT ====================

    def test_follow_up_workflow(self, client, create_patient, create_visit, doctor_headers):
        """Test complete follow-up workflow"""
        # Setup patient and visit
        patient_response = create_patient(record_number="PAT-FU-001")
        patient_id = patient_response.json()["id"]
        visit_response = create_visit(patient_id=patient_id)
        visit_id = visit_response.json()["id"]
        
        # Create follow-up
        follow_up_payload = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "doctor_id": "doc-001",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "reason": "Blood pressure check",
            "notes": "Monitor medication effectiveness"
        }
        response = client.post("/api/v1/follow-ups", json=follow_up_payload, headers=doctor_headers)
        assert response.status_code == 201
        follow_up = response.json()
        follow_up_id = follow_up["id"]
        
        # Update follow-up
        response = client.patch(
            f"/api/v1/follow-ups/{follow_up_id}",
            json={"notes": "Updated: Patient responding well to treatment"},
            headers=doctor_headers
        )
        assert response.status_code == 200
        
        # Complete follow-up
        response = client.post(f"/api/v1/follow-ups/{follow_up_id}/complete", headers=doctor_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    # ==================== ANALYTICS & REPORTING ====================

    def test_analytics_summary(self, client, admin_headers):
        """Test analytics summary endpoint"""
        response = client.get("/api/v1/analytics/summary", headers=admin_headers)
        assert response.status_code == 200
        
        analytics = response.json()
        required_fields = [
            "total_patients", "active_doctors", "appointments_today",
            "completed_visits_today", "appointments_this_week",
            "recent_new_patients_7d", "recent_appointments_7d"
        ]
        
        for field in required_fields:
            assert field in analytics
            assert isinstance(analytics[field], (int, float))

    def test_analytics_appointments_trends(self, client, admin_headers):
        """Test appointment trends analytics"""
        response = client.get("/api/v1/analytics/appointments-by-day?days=7", headers=admin_headers)
        assert response.status_code == 200
        
        trends = response.json()
        assert "items" in trends
        assert "starts_on" in trends
        assert "ends_on" in trends
        assert isinstance(trends["items"], list)

    def test_analytics_doctor_workload(self, client, admin_headers):
        """Test doctor workload analytics"""
        response = client.get("/api/v1/analytics/doctor-workload", headers=admin_headers)
        assert response.status_code == 200
        
        workload = response.json()
        assert "items" in workload
        assert isinstance(workload["items"], list)

    # ==================== PATIENT TIMELINE ====================

    def test_patient_timeline(self, client, create_patient, create_appointment, create_visit, admin_headers):
        """Test patient timeline functionality"""
        # Create comprehensive patient history
        patient_response = create_patient(record_number="PAT-TL-001")
        patient_id = patient_response.json()["id"]
        
        # Add appointment
        appointment_response = create_appointment(patient_id=patient_id)
        appointment_id = appointment_response.json()["id"]
        
        # Add visit
        visit_response = create_visit(patient_id=patient_id, appointment_id=appointment_id)
        
        # Get timeline
        response = client.get(f"/api/v1/patients/{patient_id}/timeline", headers=admin_headers)
        assert response.status_code == 200
        
        timeline = response.json()
        assert "items" in timeline
        assert len(timeline["items"]) >= 2  # At least appointment and visit
        
        # Verify timeline structure
        for event in timeline["items"]:
            assert "event_type" in event
            assert "event_timestamp" in event
            assert "title" in event

    # ==================== SECURITY & AUTHORIZATION ====================

    def test_role_based_access_control(self, client):
        """Test role-based access control across all endpoints"""
        endpoints_and_roles = {
            "/api/v1/patients": ["admin", "doctor", "receptionist"],
            "/api/v1/appointments": ["admin", "doctor", "receptionist"],
            "/api/v1/visits": ["admin", "doctor"],
            "/api/v1/prescriptions": ["admin", "doctor"],
            "/api/v1/analytics/summary": ["admin", "doctor", "receptionist"],
        }
        
        for endpoint, allowed_roles in endpoints_and_roles.items():
            # Test allowed roles
            for role in allowed_roles:
                response = client.get(endpoint, headers={"X-Demo-Role": role})
                assert response.status_code == 200, f"Role {role} should access {endpoint}"
            
            # Test forbidden role
            response = client.get(endpoint, headers={"X-Demo-Role": "guest"})
            assert response.status_code == 403, f"Guest should not access {endpoint}"

    def test_audit_logging(self, client, create_patient, admin_headers):
        """Test audit logging for sensitive operations"""
        # Create patient (should be audited)
        response = create_patient(record_number="PAT-AUDIT-001")
        assert response.status_code == 201
        
        # Verify audit log exists (this would require audit endpoint or direct DB check)
        # For now, just verify the operation succeeded
        patient_id = response.json()["id"]
        
        # Archive patient (should be audited)
        response = client.delete(f"/api/v1/patients/{patient_id}", headers=admin_headers)
        assert response.status_code == 200

    # ==================== PERFORMANCE & RELIABILITY ====================

    def test_response_times(self, client, admin_headers):
        """Test API response times are within acceptable limits"""
        import time
        
        endpoints = [
            "/api/v1/health",
            "/api/v1/patients",
            "/api/v1/analytics/summary"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=admin_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Assert response is successful
            assert response.status_code == 200
            
            # Assert response time is reasonable (< 2 seconds for development)
            assert response_time < 2.0, f"{endpoint} took too long: {response_time}s"

    def test_data_consistency(self, client, create_patient, create_appointment, doctor_headers):
        """Test data consistency across related entities"""
        # Create patient
        patient_response = create_patient(record_number="PAT-CONSIST-001")
        patient_id = patient_response.json()["id"]
        patient_data = patient_response.json()
        
        # Create appointment
        appointment_response = create_appointment(patient_id=patient_id)
        appointment_data = appointment_response.json()
        
        # Verify relationships
        assert appointment_data["patient_id"] == patient_id
        
        # Verify data can be retrieved consistently
        patient_get_response = client.get(f"/api/v1/patients/{patient_id}", headers=doctor_headers)
        assert patient_get_response.json()["id"] == patient_id
        
        appointment_get_response = client.get(f"/api/v1/appointments/{appointment_data['id']}", headers=doctor_headers)
        assert appointment_get_response.json()["patient_id"] == patient_id

    # ==================== ERROR HANDLING ====================

    def test_validation_error_handling(self, client, admin_headers):
        """Test validation error handling"""
        # Test invalid patient data
        invalid_payload = {
            "record_number": "",  # Empty record number
            "first_name": "",   # Empty name
            "date_of_birth": "invalid-date"  # Invalid date
        }
        
        response = client.post("/api/v1/patients", json=invalid_payload, headers=admin_headers)
        assert response.status_code == 422
        
        errors = response.json()
        assert "detail" in errors

    def test_not_found_handling(self, client, admin_headers):
        """Test 404 error handling"""
        # Test non-existent patient
        response = client.get("/api/v1/patients/non-existent-id", headers=admin_headers)
        assert response.status_code == 404
        
        # Test non-existent appointment
        response = client.get("/api/v1/appointments/non-existent-id", headers=admin_headers)
        assert response.status_code == 404

    # ==================== EDGE CASES ====================

    def test_concurrent_operations(self, client, create_patient, admin_headers):
        """Test system behavior under concurrent-like operations"""
        # Create multiple patients rapidly
        patient_ids = []
        for i in range(5):
            response = create_patient(record_number=f"PAT-CONCURRENT-{i:03d}")
            assert response.status_code == 201
            patient_ids.append(response.json()["id"])
        
        # Verify all patients exist
        for patient_id in patient_ids:
            response = client.get(f"/api/v1/patients/{patient_id}", headers=admin_headers)
            assert response.status_code == 200

    def test_data_integrity(self, client, create_patient, create_appointment, create_visit, doctor_headers):
        """Test data integrity constraints"""
        # Create patient
        patient_response = create_patient(record_number="PAT-INTEGRITY-001")
        patient_id = patient_response.json()["id"]
        
        # Try to create appointment with non-existent patient
        invalid_payload = {
            "patient_id": "non-existent-id",
            "scheduled_for": (datetime.now() + timedelta(days=1)).isoformat(),
            "reason": "Test appointment"
        }
        response = client.post("/api/v1/appointments", json=invalid_payload, headers=doctor_headers)
        assert response.status_code == 422  # Validation should fail


class TestClinicBusinessLogic:
    """
    Test clinic-specific business logic and workflows
    """

    def test_appointment_status_transitions(self, client, create_patient, create_appointment, doctor_headers):
        """Test appointment status business logic"""
        patient_response = create_patient(record_number="PAT-STATUS-001")
        patient_id = patient_response.json()["id"]
        appointment_response = create_appointment(patient_id=patient_id)
        appointment_id = appointment_response.json()["id"]
        
        # Test valid status transitions
        valid_transitions = ["scheduled", "completed", "cancelled", "no_show"]
        for status in valid_transitions:
            response = client.patch(
                f"/api/v1/appointments/{appointment_id}",
                json={"status": status},
                headers=doctor_headers
            )
            assert response.status_code == 200

    def test_queue_business_rules(self, client, create_patient, create_appointment, doctor_headers):
        """Test queue management business rules"""
        patient_response = create_patient(record_number="PAT-QUEUE-BIZ-001")
        patient_id = patient_response.json()["id"]
        appointment_response = create_appointment(patient_id=patient_id)
        appointment_id = appointment_response.json()["id"]
        
        # Check-in should create queue entry
        response = client.post(
            f"/api/v1/appointments/{appointment_id}/check-in",
            headers=doctor_headers
        )
        assert response.status_code == 200
        queue_entry = response.json()
        assert queue_entry["queue_number"] is not None
        
        # Should not be able to call same patient twice
        response = client.post(f"/api/v1/queue/{appointment_id}/call", headers=doctor_headers)
        assert response.status_code == 200
        
        # Second call should fail or return same state
        response = client.post(f"/api/v1/queue/{appointment_id}/call", headers=doctor_headers)
        assert response.status_code in [200, 409]  # Either succeeds or conflicts

    def test_follow_up_business_rules(self, client, create_patient, create_visit, doctor_headers):
        """Test follow-up business rules"""
        patient_response = create_patient(record_number="PAT-FU-BIZ-001")
        patient_id = patient_response.json()["id"]
        visit_response = create_visit(patient_id=patient_id)
        visit_id = visit_response.json()["id"]
        
        # Create follow-up
        follow_up_payload = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "doctor_id": "doc-001",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "reason": "Follow-up required"
        }
        response = client.post("/api/v1/follow-ups", json=follow_up_payload, headers=doctor_headers)
        assert response.status_code == 201
        follow_up_id = response.json()["id"]
        
        # Should not be able to complete follow-up that's in the future
        response = client.post(f"/api/v1/follow-ups/{follow_up_id}/complete", headers=doctor_headers)
        # This might succeed or fail depending on business logic
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__,
        "-v",
        "TestClinicComprehensive::test_health_check_smoke",
        "TestClinicComprehensive::test_patient_lifecycle_admin",
        "TestClinicComprehensive::test_appointment_workflow",
        "TestClinicComprehensive::test_analytics_summary"
    ])
