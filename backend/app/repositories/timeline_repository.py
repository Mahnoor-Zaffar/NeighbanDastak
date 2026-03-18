from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.appointment import Appointment
from app.db.models.audit_log import AuditLog
from app.db.models.patient import Patient
from app.db.models.prescription import Prescription, PrescriptionItem
from app.db.models.user import User
from app.db.models.visit import Visit


class TimelineRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_patient(self, patient_id: UUID) -> Patient | None:
        statement = select(Patient).where(Patient.id == patient_id)
        return self.session.scalar(statement)

    def get_patient_created_log(self, patient_id: UUID) -> AuditLog | None:
        statement = (
            select(AuditLog)
            .where(
                AuditLog.resource_type == "patient",
                AuditLog.resource_id == patient_id,
                AuditLog.action == "patient.create",
            )
            .order_by(AuditLog.occurred_at.desc())
        )
        return self.session.scalar(statement)

    def list_appointments_for_patient(self, patient_id: UUID) -> list[Appointment]:
        statement = select(Appointment).where(Appointment.patient_id == patient_id).order_by(Appointment.created_at)
        return list(self.session.scalars(statement))

    def list_appointment_status_change_logs(self, appointment_ids: list[UUID]) -> list[AuditLog]:
        if not appointment_ids:
            return []

        statement = (
            select(AuditLog)
            .where(
                AuditLog.resource_type == "appointment",
                AuditLog.action == "appointment.status_change",
                AuditLog.resource_id.is_not(None),
                AuditLog.resource_id.in_(appointment_ids),
            )
            .order_by(AuditLog.occurred_at)
        )
        return list(self.session.scalars(statement))

    def list_visits_for_patient(self, patient_id: UUID) -> list[Visit]:
        statement = select(Visit).where(Visit.patient_id == patient_id).order_by(Visit.created_at)
        return list(self.session.scalars(statement))

    def list_prescriptions_for_patient(self, patient_id: UUID) -> list[Prescription]:
        statement = select(Prescription).where(Prescription.patient_id == patient_id).order_by(Prescription.created_at)
        return list(self.session.scalars(statement))

    def get_users_by_ids(self, user_ids: list[UUID]) -> dict[UUID, User]:
        if not user_ids:
            return {}

        statement = select(User).where(User.id.in_(user_ids))
        users = list(self.session.scalars(statement))
        return {user.id: user for user in users}

    def get_prescription_item_counts(self, prescription_ids: list[UUID]) -> dict[UUID, int]:
        if not prescription_ids:
            return {}

        statement = (
            select(PrescriptionItem.prescription_id, func.count(PrescriptionItem.id))
            .where(PrescriptionItem.prescription_id.in_(prescription_ids))
            .group_by(PrescriptionItem.prescription_id)
        )
        rows = self.session.execute(statement).all()
        return {prescription_id: count for prescription_id, count in rows}
