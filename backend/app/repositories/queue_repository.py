from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models.appointment import Appointment, QueueStatus
from app.db.models.patient import Patient


class QueueRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_appointment_by_id(self, appointment_id: UUID) -> Appointment | None:
        statement = select(Appointment).where(Appointment.id == appointment_id)
        return self.session.scalar(statement)

    def get_patient_by_id(self, patient_id: UUID) -> Patient | None:
        statement = select(Patient).where(Patient.id == patient_id)
        return self.session.scalar(statement)

    def get_next_queue_number(self, *, scheduled_date: date, assigned_doctor_id: UUID | None) -> int:
        statement = select(func.max(Appointment.queue_number)).where(
            Appointment.scheduled_date == scheduled_date,
            Appointment.assigned_doctor_id == assigned_doctor_id,
        )
        current_max = self.session.scalar(statement)
        return int(current_max or 0) + 1

    def list_queue_entries(
        self,
        *,
        scheduled_date: date,
        assigned_doctor_id: UUID | None,
        include_history: bool,
    ) -> list[tuple[Appointment, Patient]]:
        statement = (
            select(Appointment, Patient)
            .join(Patient, Patient.id == Appointment.patient_id)
            .where(
                Appointment.scheduled_date == scheduled_date,
                Appointment.queue_status.is_not(None),
            )
        )

        if assigned_doctor_id is not None:
            statement = statement.where(Appointment.assigned_doctor_id == assigned_doctor_id)

        if not include_history:
            statement = statement.where(Appointment.queue_status.in_([QueueStatus.WAITING, QueueStatus.IN_PROGRESS]))

        queue_priority = case(
            (Appointment.queue_status == QueueStatus.IN_PROGRESS, 0),
            (Appointment.queue_status == QueueStatus.WAITING, 1),
            (Appointment.queue_status == QueueStatus.SKIPPED, 2),
            (Appointment.queue_status == QueueStatus.COMPLETED, 3),
            else_=4,
        )

        statement = statement.order_by(
            queue_priority,
            Appointment.queue_number.asc(),
            Appointment.checked_in_at.asc(),
            Appointment.created_at.asc(),
        )

        return list(self.session.execute(statement).all())

    def commit(self) -> None:
        self.session.commit()
