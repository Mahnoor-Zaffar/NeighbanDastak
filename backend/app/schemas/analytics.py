from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.appointment import AppointmentStatus


class AnalyticsSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_date: date
    scope: str
    total_patients: int
    active_doctors: int
    appointments_today: int
    completed_visits_today: int
    appointments_this_week: int
    recent_new_patients_7d: int
    recent_new_patients_previous_7d: int
    recent_appointments_7d: int
    recent_appointments_previous_7d: int


class AppointmentsByDayPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: date
    appointments_count: int


class AppointmentsByDayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_on: date
    ends_on: date
    items: list[AppointmentsByDayPoint]
    total: int


class DoctorWorkloadItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doctor_id: UUID
    doctor_name: str
    appointments_count: int


class DoctorWorkloadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_on: date
    ends_on: date
    items: list[DoctorWorkloadItem]
    total: int


class AppointmentStatusBreakdownItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AppointmentStatus
    count: int


class AppointmentStatusBreakdownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_on: date
    ends_on: date
    items: list[AppointmentStatusBreakdownItem]
    total: int
