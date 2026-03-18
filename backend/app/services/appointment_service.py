from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.appointment import Appointment, AppointmentStatus
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentRead,
    AppointmentUpdate,
)
from app.services.audit_service import AuditContext, AuditService

ALLOWED_STATUS_TRANSITIONS = {
    AppointmentStatus.SCHEDULED: {
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.COMPLETED: {AppointmentStatus.COMPLETED},
    AppointmentStatus.CANCELLED: {AppointmentStatus.CANCELLED},
    AppointmentStatus.NO_SHOW: {AppointmentStatus.NO_SHOW},
}


class AppointmentService:
    def __init__(self, session: Session):
        self.appointments = AppointmentRepository(session)
        self.patients = PatientRepository(session)
        self.visits = VisitRepository(session)
        self.audit = AuditService(session)

    def list_appointments(
        self,
        *,
        patient_id: UUID | None,
        status: AppointmentStatus | None,
        starts_at: datetime | None,
        ends_at: datetime | None,
        limit: int,
        offset: int,
    ) -> AppointmentListResponse:
        items, total = self.appointments.list(
            patient_id=patient_id,
            status=status,
            starts_at=starts_at,
            ends_at=ends_at,
            limit=limit,
            offset=offset,
        )
        return AppointmentListResponse(
            items=[AppointmentRead.model_validate(item) for item in items],
            total=total,
        )

    def get_appointment(self, appointment_id: UUID) -> AppointmentRead:
        appointment = self.appointments.get_by_id(appointment_id)
        if appointment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        return AppointmentRead.model_validate(appointment)

    def create_appointment(self, payload: AppointmentCreate, *, context: AuditContext) -> AppointmentRead:
        patient = self.patients.get_by_id(payload.patient_id)
        if patient is None or patient.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        if payload.scheduled_for <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="scheduled_for must be in the future",
            )

        appointment = Appointment(
            patient_id=payload.patient_id,
            scheduled_for=payload.scheduled_for,
            scheduled_date=payload.scheduled_for.date(),
            status=AppointmentStatus.SCHEDULED,
            reason=payload.reason,
            notes=payload.notes,
        )
        appointment = self.appointments.create(appointment)
        self.audit.log_action(
            context=context,
            action="appointment.create",
            resource_type="appointment",
            resource_id=appointment.id,
            metadata={"status": appointment.status.value},
        )
        self.appointments.commit()
        return AppointmentRead.model_validate(appointment)

    def update_appointment(
        self,
        appointment_id: UUID,
        payload: AppointmentUpdate,
        *,
        context: AuditContext,
    ) -> AppointmentRead:
        appointment = self.appointments.get_by_id(appointment_id)
        if appointment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        updates = payload.model_dump(exclude_unset=True)
        if "patient_id" in updates:
            patient = self.patients.get_by_id(updates["patient_id"])
            if patient is None or patient.archived_at is not None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        if "scheduled_for" in updates and updates["scheduled_for"] <= datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="scheduled_for must be in the future",
            )

        current_status = appointment.status
        next_status = updates.get("status")
        if next_status is not None:
            allowed_statuses = ALLOWED_STATUS_TRANSITIONS[appointment.status]
            if next_status not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot change appointment status from {appointment.status} to {next_status}",
                )

        for field, value in updates.items():
            setattr(appointment, field, value)
        if "scheduled_for" in updates:
            appointment.scheduled_date = appointment.scheduled_for.date()

        if next_status is not None and next_status != current_status:
            self.audit.log_action(
                context=context,
                action="appointment.status_change",
                resource_type="appointment",
                resource_id=appointment.id,
                metadata={"from_status": current_status.value, "to_status": next_status.value},
            )
        else:
            self.audit.log_action(
                context=context,
                action="appointment.update",
                resource_type="appointment",
                resource_id=appointment.id,
                metadata={"changed_fields": sorted(updates.keys())},
            )
        self.appointments.commit()
        return AppointmentRead.model_validate(appointment)

    def delete_appointment(self, appointment_id: UUID, *, context: AuditContext) -> None:
        appointment = self.appointments.get_by_id(appointment_id)
        if appointment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        linked_visit = self.visits.get_by_appointment_id(appointment.id)
        if linked_visit is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete appointment with a linked visit",
            )

        self.audit.log_action(
            context=context,
            action="appointment.delete",
            resource_type="appointment",
            resource_id=appointment.id,
        )
        self.appointments.delete(appointment)
        self.appointments.commit()
