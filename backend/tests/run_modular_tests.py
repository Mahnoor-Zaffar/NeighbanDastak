#!/usr/bin/env python3
"""
Modular Test Runner for Clinic Management System

Usage:
    python tests/run_modular_tests.py --category smoke
    python tests/run_modular_tests.py --category integration  
    python tests/run_modular_tests.py --category business
    python tests/run_modular_tests.py --category security
    python tests/run_modular_tests.py --category performance
    python tests/run_modular_tests.py --category all

Categories:
    smoke: Basic functionality verification
    integration: Cross-module workflow testing
    business: Business logic validation
    security: Role-based access control
    performance: Response time and load testing
    all: Run all test categories
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        # Activate virtual environment and run command
        full_command = f"source ../.venv/bin/activate && {command}"
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def run_smoke_tests():
    """Run basic smoke tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_health_check_smoke -v", 
         "Health Check Smoke Test"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_api_accessibility_smoke -v", 
         "API Accessibility Smoke Test"),
        ("pytest test_health.py -v", 
         "Health Endpoint Tests"),
        ("pytest test_auth_api.py -v", 
         "Authentication API Tests"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Smoke Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_integration_tests():
    """Run integration tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_patient_lifecycle_admin -v", 
         "Patient Lifecycle Integration"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_appointment_workflow -v", 
         "Appointment Workflow Integration"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_visit_documentation_workflow -v", 
         "Visit Documentation Integration"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_prescription_workflow -v", 
         "Prescription Workflow Integration"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_follow_up_workflow -v", 
         "Follow-up Workflow Integration"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_patient_timeline -v", 
         "Patient Timeline Integration"),
        ("pytest test_integration_flows.py -v", 
         "Integration Flow Tests"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Integration Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_business_logic_tests():
    """Run business logic tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicBusinessLogic::test_appointment_status_transitions -v", 
         "Appointment Status Transitions"),
        ("pytest test_clinic_comprehensive.py::TestClinicBusinessLogic::test_queue_business_rules -v", 
         "Queue Business Rules"),
        ("pytest test_clinic_comprehensive.py::TestClinicBusinessLogic::test_follow_up_business_rules -v", 
         "Follow-up Business Rules"),
        ("pytest test_patients.py -v", 
         "Patient Business Logic"),
        ("pytest test_appointments_visits.py -v", 
         "Appointment & Visit Business Logic"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Business Logic Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_security_tests():
    """Run security and authorization tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_role_based_access_control -v", 
         "Role-Based Access Control"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_audit_logging -v", 
         "Audit Logging Security"),
        ("pytest test_security_audit.py -v", 
         "Security Audit Tests"),
        ("pytest test_rate_limit.py -v", 
         "Rate Limiting Security"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Security Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_performance_tests():
    """Run performance and reliability tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_response_times -v", 
         "API Response Times"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_data_consistency -v", 
         "Data Consistency"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_concurrent_operations -v", 
         "Concurrent Operations"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_data_integrity -v", 
         "Data Integrity"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Performance Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_analytics_tests():
    """Run analytics and reporting tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_analytics_summary -v", 
         "Analytics Summary"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_analytics_appointments_trends -v", 
         "Appointment Trends Analytics"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_analytics_doctor_workload -v", 
         "Doctor Workload Analytics"),
        ("pytest test_analytics.py -v", 
         "Analytics Module Tests"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Analytics Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_error_handling_tests():
    """Run error handling and edge case tests"""
    tests = [
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_validation_error_handling -v", 
         "Validation Error Handling"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_not_found_handling -v", 
         "404 Error Handling"),
        ("pytest test_clinic_comprehensive.py::TestClinicComprehensive::test_edge_cases -v", 
         "Edge Cases"),
        ("pytest test_schema_validation.py -v", 
         "Schema Validation Tests"),
    ]
    
    success_count = 0
    for command, description in tests:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Error Handling Tests: {success_count}/{len(tests)} passed")
    print(f"{'='*60}")
    return success_count == len(tests)


def run_all_tests():
    """Run all test categories"""
    print("🚀 Running Complete Test Suite")
    print("This will take several minutes...")
    
    categories = [
        ("Smoke Tests", run_smoke_tests),
        ("Integration Tests", run_integration_tests), 
        ("Business Logic Tests", run_business_logic_tests),
        ("Security Tests", run_security_tests),
        ("Performance Tests", run_performance_tests),
        ("Analytics Tests", run_analytics_tests),
        ("Error Handling Tests", run_error_handling_tests),
    ]
    
    results = []
    for category_name, test_func in categories:
        print(f"\n🔍 {category_name}")
        result = test_func()
        results.append((category_name, result))
    
    # Summary
    print(f"\n{'='*80}")
    print("🏁 FINAL TEST RESULTS")
    print(f"{'='*80}")
    
    passed_categories = sum(1 for _, result in results if result)
    total_categories = len(results)
    
    for category_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{category_name}: {status}")
    
    print(f"\nOverall: {passed_categories}/{total_categories} categories passed")
    
    if passed_categories == total_categories:
        print("🎉 All test categories passed! System is ready for deployment.")
        return True
    else:
        print("⚠️  Some test categories failed. Review the failures above.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Modular Test Runner for Clinic Management System")
    parser.add_argument(
        "--category",
        choices=["smoke", "integration", "business", "security", "performance", "analytics", "error", "all"],
        default="smoke",
        help="Test category to run"
    )
    
    args = parser.parse_args()
    
    print("🧪 Clinic Management System - Modular Test Runner")
    print("=" * 50)
    
    success = True
    
    if args.category == "smoke":
        success = run_smoke_tests()
    elif args.category == "integration":
        success = run_integration_tests()
    elif args.category == "business":
        success = run_business_logic_tests()
    elif args.category == "security":
        success = run_security_tests()
    elif args.category == "performance":
        success = run_performance_tests()
    elif args.category == "analytics":
        success = run_analytics_tests()
    elif args.category == "error":
        success = run_error_handling_tests()
    elif args.category == "all":
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
