from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor
from app.db.models.appointment import AppointmentStatus
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import (
    AppointmentStatusBreakdownItem,
    AppointmentStatusBreakdownResponse,
    AnalyticsSummaryResponse,
    AppointmentsByDayPoint,
    AppointmentsByDayResponse,
    DoctorWorkloadItem,
    DoctorWorkloadResponse,
)


class AnalyticsService:
    def __init__(self, session: Session):
        self.repository = AnalyticsRepository(session)

    def get_summary(self, *, actor: QueueActor, doctor_id: UUID | None = None) -> AnalyticsSummaryResponse:
        doctor_scope = self._resolve_doctor_scope(actor, doctor_id)
        today = self._today()
        week_start = self._week_start(today)
        week_end = week_start + timedelta(days=6)

        return AnalyticsSummaryResponse(
            reference_date=today,
            scope="doctor" if doctor_scope is not None else "clinic",
            total_patients=self.repository.count_total_patients(doctor_id=doctor_scope),
            active_doctors=self.repository.count_active_doctors(doctor_id=doctor_scope),
            appointments_today=self.repository.count_appointments_on_date(
                scheduled_date=today,
                doctor_id=doctor_scope,
            ),
            completed_visits_today=self.repository.count_completed_visits_on_date(
                reference_date=today,
                doctor_id=doctor_scope,
            ),
            appointments_this_week=self.repository.count_appointments_between(
                starts_on=week_start,
                ends_on=week_end,
                doctor_id=doctor_scope,
            ),
            recent_new_patients_7d=self.repository.count_recent_new_patients_7d(
                reference_date=today,
                doctor_id=doctor_scope,
            ),
            recent_new_patients_previous_7d=self.repository.count_recent_new_patients_previous_7d(
                reference_date=today,
                doctor_id=doctor_scope,
            ),
            recent_appointments_7d=self.repository.count_recent_appointments_7d(
                reference_date=today,
                doctor_id=doctor_scope,
            ),
            recent_appointments_previous_7d=self.repository.count_recent_appointments_previous_7d(
                reference_date=today,
                doctor_id=doctor_scope,
            ),
        )

    def get_appointments_by_day(
        self,
        *,
        actor: QueueActor,
        days: int,
        ends_on: date | None,
        doctor_id: UUID | None,
    ) -> AppointmentsByDayResponse:
        doctor_scope = self._resolve_doctor_scope(actor, doctor_id)
        effective_end = ends_on or self._today()
        effective_start = effective_end - timedelta(days=days - 1)

        rows = self.repository.list_appointments_by_day(
            starts_on=effective_start,
            ends_on=effective_end,
            doctor_id=doctor_scope,
        )
        counts_by_day = {day: count for day, count in rows}
        items = [
            AppointmentsByDayPoint(
                day=day,
                appointments_count=counts_by_day.get(day, 0),
            )
            for day in self._date_range(effective_start, effective_end)
        ]
        return AppointmentsByDayResponse(
            starts_on=effective_start,
            ends_on=effective_end,
            items=items,
            total=len(items),
        )

    def get_doctor_workload(
        self,
        *,
        actor: QueueActor,
        starts_on: date | None,
        ends_on: date | None,
        doctor_id: UUID | None,
    ) -> DoctorWorkloadResponse:
        doctor_scope = self._resolve_doctor_scope(actor, doctor_id)
        effective_start, effective_end = self._resolve_date_range(starts_on=starts_on, ends_on=ends_on)

        rows = self.repository.list_doctor_workload(
            starts_on=effective_start,
            ends_on=effective_end,
            doctor_id=doctor_scope,
        )
        items = [
            DoctorWorkloadItem(
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                appointments_count=appointments_count,
            )
            for doctor_id, doctor_name, appointments_count in rows
        ]
        return DoctorWorkloadResponse(
            starts_on=effective_start,
            ends_on=effective_end,
            items=items,
            total=len(items),
        )

    def get_appointment_status_breakdown(
        self,
        *,
        actor: QueueActor,
        starts_on: date | None,
        ends_on: date | None,
        doctor_id: UUID | None,
    ) -> AppointmentStatusBreakdownResponse:
        doctor_scope = self._resolve_doctor_scope(actor, doctor_id)
        effective_start, effective_end = self._resolve_date_range(starts_on=starts_on, ends_on=ends_on)

        rows = self.repository.list_appointment_status_breakdown(
            starts_on=effective_start,
            ends_on=effective_end,
            doctor_id=doctor_scope,
        )
        counts_by_status = {status: count for status, count in rows}
        items = [
            AppointmentStatusBreakdownItem(
                status=status,
                count=counts_by_status.get(status, 0),
            )
            for status in AppointmentStatus
        ]
        return AppointmentStatusBreakdownResponse(
            starts_on=effective_start,
            ends_on=effective_end,
            items=items,
            total=len(items),
        )

    def _resolve_doctor_scope(self, actor: QueueActor, doctor_id: UUID | None) -> UUID | None:
        if actor.role in {"admin", "receptionist"}:
            if doctor_id is None:
                return None
            doctor = self.repository.get_active_doctor(doctor_id)
            if doctor is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
            return doctor_id
        if actor.role != "doctor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        if actor.user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor identity is required",
            )
        doctor = self.repository.get_active_doctor(actor.user_id)
        if doctor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        if doctor_id is not None and doctor_id != actor.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor cannot access another doctor's analytics",
            )
        return actor.user_id

    def _resolve_date_range(self, *, starts_on: date | None, ends_on: date | None) -> tuple[date, date]:
        if starts_on is None and ends_on is None:
            current = self._today()
            week_start = self._week_start(current)
            return week_start, week_start + timedelta(days=6)

        current = self._today()
        effective_start = starts_on or (ends_on - timedelta(days=6) if ends_on is not None else current - timedelta(days=6))
        effective_end = ends_on or (starts_on + timedelta(days=6) if starts_on is not None else current)
        if effective_start > effective_end:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="starts_on cannot be after ends_on")
        return effective_start, effective_end

    def _today(self) -> date:
        return datetime.now(UTC).date()

    def _week_start(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _date_range(self, starts_on: date, ends_on: date) -> list[date]:
        total_days = (ends_on - starts_on).days + 1
        return [starts_on + timedelta(days=offset) for offset in range(total_days)]
