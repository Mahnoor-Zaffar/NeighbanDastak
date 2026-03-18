from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor
from app.core.rbac import Role
from app.db.models.appointment import Appointment, AppointmentStatus, QueueStatus
from app.repositories.queue_repository import QueueRepository
from app.repositories.user_repository import UserRepository
from app.schemas.queue import QueueCheckInRequest, QueueEntryRead, QueueListResponse
from app.services.audit_service import AuditContext, AuditService

ALLOWED_QUEUE_TRANSITIONS: dict[QueueStatus | None, set[QueueStatus]] = {
    None: {QueueStatus.WAITING},
    QueueStatus.WAITING: {QueueStatus.IN_PROGRESS, QueueStatus.SKIPPED},
    QueueStatus.IN_PROGRESS: {QueueStatus.COMPLETED, QueueStatus.SKIPPED},
    QueueStatus.COMPLETED: set(),
    QueueStatus.SKIPPED: set(),
}


class QueueService:
    def __init__(self, session: Session):
        self.queue = QueueRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    def check_in(
        self,
        appointment_id: UUID,
        payload: QueueCheckInRequest,
        *,
        actor: QueueActor,
        context: AuditContext,
    ) -> QueueEntryRead:
        appointment = self._get_appointment_or_404(appointment_id)
        assigned_doctor_id = payload.assigned_doctor_id or appointment.assigned_doctor_id

        self._enforce_manage_permission(actor, appointment, assigned_doctor_id=assigned_doctor_id)
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only scheduled appointments can be checked in",
            )
        if appointment.queue_status is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment is already checked in")
        if assigned_doctor_id is not None:
            self._validate_doctor(assigned_doctor_id)

        scheduled_date = appointment.scheduled_date
        queue_number = self.queue.get_next_queue_number(
            scheduled_date=scheduled_date,
            assigned_doctor_id=assigned_doctor_id,
        )
        appointment.queue_number = queue_number
        appointment.queue_status = QueueStatus.WAITING
        appointment.checked_in_at = datetime.now(UTC)
        appointment.called_at = None
        appointment.completed_at = None
        appointment.assigned_doctor_id = assigned_doctor_id

        self.audit.log_action(
            context=context,
            action="queue.check_in",
            resource_type="appointment",
            resource_id=appointment.id,
            metadata={
                "queue_number": queue_number,
                "assigned_doctor_id": str(assigned_doctor_id) if assigned_doctor_id else None,
            },
        )
        self.queue.commit()
        return self._build_queue_entry(appointment)

    def list_queue(
        self,
        *,
        actor: QueueActor,
        scheduled_date: date,
        doctor_id: UUID | None,
        include_history: bool,
    ) -> QueueListResponse:
        resolved_doctor_id = doctor_id
        if actor.role == "doctor":
            if actor.user_id is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor identity is required")
            if doctor_id is not None and doctor_id != actor.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Doctors can only view their own queue",
                )
            resolved_doctor_id = actor.user_id

        rows = self.queue.list_queue_entries(
            scheduled_date=scheduled_date,
            assigned_doctor_id=resolved_doctor_id,
            include_history=include_history,
        )

        return QueueListResponse(
            scheduled_date=scheduled_date,
            doctor_id=resolved_doctor_id,
            include_history=include_history,
            items=[
                self._build_queue_entry(
                    appointment,
                    patient_name_override=f"{patient.first_name} {patient.last_name}",
                    patient_record_number_override=patient.record_number,
                )
                for appointment, patient in rows
            ],
            total=len(rows),
        )

    def call_next(
        self,
        appointment_id: UUID,
        *,
        actor: QueueActor,
        context: AuditContext,
    ) -> QueueEntryRead:
        return self._transition_status(
            appointment_id=appointment_id,
            next_status=QueueStatus.IN_PROGRESS,
            actor=actor,
            context=context,
            action="queue.call",
        )

    def complete(
        self,
        appointment_id: UUID,
        *,
        actor: QueueActor,
        context: AuditContext,
    ) -> QueueEntryRead:
        return self._transition_status(
            appointment_id=appointment_id,
            next_status=QueueStatus.COMPLETED,
            actor=actor,
            context=context,
            action="queue.complete",
        )

    def skip(
        self,
        appointment_id: UUID,
        *,
        actor: QueueActor,
        context: AuditContext,
    ) -> QueueEntryRead:
        return self._transition_status(
            appointment_id=appointment_id,
            next_status=QueueStatus.SKIPPED,
            actor=actor,
            context=context,
            action="queue.skip",
        )

    def _transition_status(
        self,
        *,
        appointment_id: UUID,
        next_status: QueueStatus,
        actor: QueueActor,
        context: AuditContext,
        action: str,
    ) -> QueueEntryRead:
        appointment = self._get_appointment_or_404(appointment_id)
        self._enforce_manage_permission(actor, appointment)

        allowed_targets = ALLOWED_QUEUE_TRANSITIONS.get(appointment.queue_status, set())
        if next_status not in allowed_targets:
            from_status = appointment.queue_status.value if appointment.queue_status is not None else "none"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot change queue status from {from_status} to {next_status.value}",
            )

        appointment.queue_status = next_status
        if next_status == QueueStatus.IN_PROGRESS:
            appointment.called_at = datetime.now(UTC)
        if next_status in {QueueStatus.COMPLETED, QueueStatus.SKIPPED}:
            appointment.completed_at = datetime.now(UTC)
            appointment.status = (
                AppointmentStatus.COMPLETED if next_status == QueueStatus.COMPLETED else AppointmentStatus.NO_SHOW
            )

        self.audit.log_action(
            context=context,
            action=action,
            resource_type="appointment",
            resource_id=appointment.id,
            metadata={"queue_status": appointment.queue_status.value},
        )
        self.queue.commit()
        return self._build_queue_entry(appointment)

    def _get_appointment_or_404(self, appointment_id: UUID) -> Appointment:
        appointment = self.queue.get_appointment_by_id(appointment_id)
        if appointment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        return appointment

    def _validate_doctor(self, doctor_id: UUID) -> None:
        user = self.users.get_by_id(doctor_id)
        if user is None or user.role != Role.DOCTOR or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    def _enforce_manage_permission(
        self,
        actor: QueueActor,
        appointment: Appointment,
        *,
        assigned_doctor_id: UUID | None = None,
    ) -> None:
        if actor.role in {"admin", "receptionist"}:
            return

        if actor.user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor identity is required")

        expected_doctor_id = assigned_doctor_id if assigned_doctor_id is not None else appointment.assigned_doctor_id
        if expected_doctor_id is None or expected_doctor_id != actor.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors can only manage their assigned queue",
            )

    def _build_queue_entry(
        self,
        appointment: Appointment,
        *,
        patient_name_override: str | None = None,
        patient_record_number_override: str | None = None,
    ) -> QueueEntryRead:
        if appointment.queue_status is None or appointment.queue_number is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment is not in queue")

        patient_name = patient_name_override
        patient_record_number = patient_record_number_override

        if patient_name is None or patient_record_number is None:
            patient = self.queue.get_patient_by_id(appointment.patient_id)
            if patient is not None:
                patient_name = f"{patient.first_name} {patient.last_name}"
                patient_record_number = patient.record_number

        if patient_name is None or patient_record_number is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        return QueueEntryRead(
            appointment_id=appointment.id,
            patient_id=appointment.patient_id,
            patient_record_number=patient_record_number,
            patient_name=patient_name,
            scheduled_for=appointment.scheduled_for,
            scheduled_date=appointment.scheduled_date,
            appointment_status=appointment.status,
            queue_number=appointment.queue_number,
            queue_status=appointment.queue_status,
            checked_in_at=appointment.checked_in_at,
            called_at=appointment.called_at,
            completed_at=appointment.completed_at,
            assigned_doctor_id=appointment.assigned_doctor_id,
        )
