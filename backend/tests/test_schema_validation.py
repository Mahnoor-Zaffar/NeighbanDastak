from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.schemas.patient import PatientCreate
from app.schemas.visit import VisitCreate, VisitUpdate


def test_patient_schema_normalizes_record_number_and_names() -> None:
    payload = PatientCreate(
        record_number="  pat-777  ",
        first_name="  Nadia ",
        last_name=" Shah  ",
        date_of_birth="1992-06-11",
        email="nadia@example.com",
        phone="+1 555 0333",
        city=" Karachi ",
        notes=" Follow-up record ",
    )

    assert payload.record_number == "PAT-777"
    assert payload.first_name == "Nadia"
    assert payload.last_name == "Shah"
    assert payload.city == "Karachi"
    assert payload.notes == "Follow-up record"


def test_patient_schema_rejects_blank_optional_text_values() -> None:
    with pytest.raises(ValidationError):
        PatientCreate(
            record_number="PAT-778",
            first_name="Amina",
            last_name="Khan",
            date_of_birth="1992-06-11",
            notes="   ",
        )


def test_appointment_schema_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValidationError):
        AppointmentCreate(
            patient_id=uuid4(),
            scheduled_for=datetime.now(),  # noqa: DTZ005
        )


def test_appointment_update_normalizes_empty_reason_notes_to_none() -> None:
    payload = AppointmentUpdate(
        reason="   ",
        notes="",
    )

    assert payload.reason is None
    assert payload.notes is None


def test_visit_create_rejects_inverted_time_window() -> None:
    start = datetime.now(UTC)
    with pytest.raises(ValidationError):
        VisitCreate(
            patient_id=uuid4(),
            started_at=start,
            ended_at=start - timedelta(hours=1),
        )


def test_visit_update_rejects_naive_timestamps() -> None:
    with pytest.raises(ValidationError):
        VisitUpdate(started_at=datetime.now())  # noqa: DTZ005
