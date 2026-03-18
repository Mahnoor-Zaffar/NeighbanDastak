from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.appointment import AppointmentStatus, QueueStatus


class QueueCheckInRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assigned_doctor_id: UUID | None = None


class QueueEntryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_id: UUID
    patient_id: UUID
    patient_record_number: str
    patient_name: str
    scheduled_for: datetime
    scheduled_date: date
    appointment_status: AppointmentStatus
    queue_number: int
    queue_status: QueueStatus
    checked_in_at: datetime | None
    called_at: datetime | None
    completed_at: datetime | None
    assigned_doctor_id: UUID | None


class QueueListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheduled_date: date
    doctor_id: UUID | None
    include_history: bool
    items: list[QueueEntryRead]
    total: int
