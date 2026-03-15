from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.appointment import AppointmentStatus
from app.db.models.visit import Visit
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.visit import VisitCreate, VisitRead, VisitUpdate
from app.services.audit_service import AuditContext, AuditService


class VisitService:
    def __init__(self, session: Session):
        self.visits = VisitRepository(session)
        self.patients = PatientRepository(session)
        self.appointments = AppointmentRepository(session)
        self.audit = AuditService(session)

    def create_visit(self, payload: VisitCreate, *, context: AuditContext) -> VisitRead:
        patient = self.patients.get_by_id(payload.patient_id)
        if patient is None or patient.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        if payload.ended_at is not None and payload.ended_at < payload.started_at:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="ended_at cannot be before started_at",
            )

        appointment = None
        if payload.appointment_id is not None:
            appointment = self.appointments.get_by_id(payload.appointment_id)
            if appointment is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
            if appointment.patient_id != payload.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="appointment does not belong to the provided patient",
                )
            if self.visits.get_by_appointment_id(appointment.id) is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A visit already exists for this appointment",
                )
            if appointment.status in {AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot create a visit for a cancelled or no-show appointment",
                )

        visit = Visit(
            patient_id=payload.patient_id,
            appointment_id=payload.appointment_id,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            complaint=payload.complaint,
            diagnosis_summary=payload.diagnosis_summary,
            notes=payload.notes,
        )
        visit = self.visits.create(visit)

        if appointment is not None and appointment.status == AppointmentStatus.SCHEDULED:
            appointment.status = AppointmentStatus.COMPLETED

        self.audit.log_action(
            context=context,
            action="visit.create",
            resource_type="visit",
            resource_id=visit.id,
            metadata={"linked_appointment": payload.appointment_id is not None},
        )
        self.visits.commit()
        return VisitRead.model_validate(visit)

    def get_visit(self, visit_id: UUID) -> VisitRead:
        visit = self.visits.get_by_id(visit_id)
        if visit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

        return VisitRead.model_validate(visit)

    def update_visit(self, visit_id: UUID, payload: VisitUpdate, *, context: AuditContext) -> VisitRead:
        visit = self.visits.get_by_id(visit_id)
        if visit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

        updates = payload.model_dump(exclude_unset=True)
        started_at = updates.get("started_at", visit.started_at)
        ended_at = updates.get("ended_at", visit.ended_at)
        if ended_at is not None and ended_at < started_at:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="ended_at cannot be before started_at",
            )

        for field, value in updates.items():
            setattr(visit, field, value)

        self.audit.log_action(
            context=context,
            action="visit.update",
            resource_type="visit",
            resource_id=visit.id,
            metadata={"changed_fields": sorted(updates.keys())},
        )
        self.visits.commit()
        return VisitRead.model_validate(visit)
