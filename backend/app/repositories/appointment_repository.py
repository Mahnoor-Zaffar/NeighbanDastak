from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.models.appointment import Appointment, AppointmentStatus


class AppointmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, appointment: Appointment) -> Appointment:
        self.session.add(appointment)
        self.session.flush()
        self.session.refresh(appointment)
        return appointment

    def get_by_id(self, appointment_id: UUID) -> Appointment | None:
        statement = select(Appointment).where(Appointment.id == appointment_id)
        return self.session.scalar(statement)

    def list(
        self,
        *,
        patient_id: UUID | None,
        status: AppointmentStatus | None,
        starts_at: datetime | None,
        ends_at: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Appointment], int]:
        statement = select(Appointment)
        count_statement = select(func.count()).select_from(Appointment)
        filters = []

        if patient_id is not None:
            filters.append(Appointment.patient_id == patient_id)
        if status is not None:
            filters.append(Appointment.status == status)
        if starts_at is not None:
            filters.append(Appointment.scheduled_for >= starts_at)
        if ends_at is not None:
            filters.append(Appointment.scheduled_for <= ends_at)

        if filters:
            where_clause = and_(*filters)
            statement = statement.where(where_clause)
            count_statement = count_statement.where(where_clause)

        statement = statement.order_by(Appointment.scheduled_for).offset(offset).limit(limit)

        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def delete(self, appointment: Appointment) -> None:
        self.session.delete(appointment)

    def commit(self) -> None:
        self.session.commit()
