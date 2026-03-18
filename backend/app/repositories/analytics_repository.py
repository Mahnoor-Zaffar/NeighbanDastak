from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.db.models.appointment import Appointment, AppointmentStatus
from app.db.models.patient import Patient
from app.db.models.user import User
from app.db.models.visit import Visit


class AnalyticsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_doctor(self, doctor_id: UUID) -> User | None:
        statement = select(User).where(
            User.id == doctor_id,
            User.role == Role.DOCTOR,
            User.is_active.is_(True),
        )
        return self.session.scalar(statement)

    def count_total_patients(self, *, doctor_id: UUID | None) -> int:
        if doctor_id is None:
            statement = select(func.count()).select_from(Patient).where(Patient.archived_at.is_(None))
            return int(self.session.scalar(statement) or 0)

        statement = (
            select(func.count(func.distinct(Appointment.patient_id)))
            .select_from(Appointment)
            .join(Patient, Patient.id == Appointment.patient_id)
            .where(
                Appointment.assigned_doctor_id == doctor_id,
                Patient.archived_at.is_(None),
            )
        )
        return int(self.session.scalar(statement) or 0)

    def count_active_doctors(self, *, doctor_id: UUID | None) -> int:
        statement = select(func.count()).select_from(User).where(
            User.role == Role.DOCTOR,
            User.is_active.is_(True),
        )
        if doctor_id is not None:
            statement = statement.where(User.id == doctor_id)
        return int(self.session.scalar(statement) or 0)

    def count_appointments_on_date(self, *, scheduled_date: date, doctor_id: UUID | None) -> int:
        statement = select(func.count()).select_from(Appointment).where(Appointment.scheduled_date == scheduled_date)
        if doctor_id is not None:
            statement = statement.where(Appointment.assigned_doctor_id == doctor_id)
        return int(self.session.scalar(statement) or 0)

    def count_appointments_between(
        self,
        *,
        starts_on: date,
        ends_on: date,
        doctor_id: UUID | None,
    ) -> int:
        statement = select(func.count()).select_from(Appointment).where(
            Appointment.scheduled_date >= starts_on,
            Appointment.scheduled_date <= ends_on,
        )
        if doctor_id is not None:
            statement = statement.where(Appointment.assigned_doctor_id == doctor_id)
        return int(self.session.scalar(statement) or 0)

    def count_completed_visits_on_date(self, *, reference_date: date, doctor_id: UUID | None) -> int:
        date_literal = reference_date.isoformat()
        statement = (
            select(func.count())
            .select_from(Visit)
            .where(
                Visit.ended_at.is_not(None),
                func.date(Visit.ended_at) == date_literal,
            )
        )
        if doctor_id is not None:
            statement = statement.join(Appointment, Appointment.id == Visit.appointment_id).where(
                Appointment.assigned_doctor_id == doctor_id
            )
        return int(self.session.scalar(statement) or 0)

    def count_recent_new_patients_7d(self, *, reference_date: date, doctor_id: UUID | None) -> int:
        starts_on = reference_date - timedelta(days=6)
        if doctor_id is None:
            statement = select(func.count()).select_from(Patient).where(
                Patient.archived_at.is_(None),
                func.date(Patient.created_at) >= starts_on.isoformat(),
                func.date(Patient.created_at) <= reference_date.isoformat(),
            )
            return int(self.session.scalar(statement) or 0)

        statement = (
            select(func.count(func.distinct(Appointment.patient_id)))
            .select_from(Appointment)
            .where(
                Appointment.assigned_doctor_id == doctor_id,
                Appointment.scheduled_date >= starts_on,
                Appointment.scheduled_date <= reference_date,
            )
        )
        return int(self.session.scalar(statement) or 0)

    def count_recent_new_patients_previous_7d(self, *, reference_date: date, doctor_id: UUID | None) -> int:
        window_end = reference_date - timedelta(days=7)
        window_start = window_end - timedelta(days=6)
        if doctor_id is None:
            statement = select(func.count()).select_from(Patient).where(
                Patient.archived_at.is_(None),
                func.date(Patient.created_at) >= window_start.isoformat(),
                func.date(Patient.created_at) <= window_end.isoformat(),
            )
            return int(self.session.scalar(statement) or 0)

        statement = (
            select(func.count(func.distinct(Appointment.patient_id)))
            .select_from(Appointment)
            .where(
                Appointment.assigned_doctor_id == doctor_id,
                Appointment.scheduled_date >= window_start,
                Appointment.scheduled_date <= window_end,
            )
        )
        return int(self.session.scalar(statement) or 0)

    def count_recent_appointments_7d(self, *, reference_date: date, doctor_id: UUID | None) -> int:
        starts_on = reference_date - timedelta(days=6)
        return self.count_appointments_between(starts_on=starts_on, ends_on=reference_date, doctor_id=doctor_id)

    def count_recent_appointments_previous_7d(self, *, reference_date: date, doctor_id: UUID | None) -> int:
        window_end = reference_date - timedelta(days=7)
        window_start = window_end - timedelta(days=6)
        return self.count_appointments_between(starts_on=window_start, ends_on=window_end, doctor_id=doctor_id)

    def list_appointments_by_day(
        self,
        *,
        starts_on: date,
        ends_on: date,
        doctor_id: UUID | None,
    ) -> list[tuple[date, int]]:
        statement = (
            select(
                Appointment.scheduled_date,
                func.count(Appointment.id),
            )
            .where(
                Appointment.scheduled_date >= starts_on,
                Appointment.scheduled_date <= ends_on,
            )
            .group_by(Appointment.scheduled_date)
            .order_by(Appointment.scheduled_date.asc())
        )
        if doctor_id is not None:
            statement = statement.where(Appointment.assigned_doctor_id == doctor_id)

        return [(scheduled_date, int(count)) for scheduled_date, count in self.session.execute(statement).all()]

    def list_doctor_workload(
        self,
        *,
        starts_on: date,
        ends_on: date,
        doctor_id: UUID | None,
    ) -> list[tuple[UUID, str, int]]:
        join_condition = and_(
            Appointment.assigned_doctor_id == User.id,
            Appointment.scheduled_date >= starts_on,
            Appointment.scheduled_date <= ends_on,
        )
        statement = (
            select(
                User.id,
                User.full_name,
                func.count(Appointment.id).label("appointments_count"),
            )
            .select_from(User)
            .outerjoin(Appointment, join_condition)
            .where(
                User.role == Role.DOCTOR,
                User.is_active.is_(True),
            )
            .group_by(User.id, User.full_name)
            .order_by(func.count(Appointment.id).desc(), User.full_name.asc())
        )
        if doctor_id is not None:
            statement = statement.where(User.id == doctor_id)

        rows = self.session.execute(statement).all()
        return [(doctor_id_row, doctor_name, int(appointment_count or 0)) for doctor_id_row, doctor_name, appointment_count in rows]

    def list_appointment_status_breakdown(
        self,
        *,
        starts_on: date,
        ends_on: date,
        doctor_id: UUID | None,
    ) -> list[tuple[AppointmentStatus, int]]:
        statement = (
            select(
                Appointment.status,
                func.count(Appointment.id).label("status_count"),
            )
            .where(
                Appointment.scheduled_date >= starts_on,
                Appointment.scheduled_date <= ends_on,
            )
            .group_by(Appointment.status)
        )
        if doctor_id is not None:
            statement = statement.where(Appointment.assigned_doctor_id == doctor_id)

        return [(status, int(count or 0)) for status, count in self.session.execute(statement).all()]
