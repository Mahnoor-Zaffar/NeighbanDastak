from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor
from app.core.rbac import Role
from app.db.models.follow_up import FollowUp, FollowUpStatus
from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.follow_up import FollowUpCreate, FollowUpListResponse, FollowUpRead, FollowUpUpdate
from app.services.audit_service import AuditContext, AuditService

ALLOWED_ACTION_SOURCE_STATUSES = {FollowUpStatus.PENDING, FollowUpStatus.OVERDUE}


class FollowUpService:
    def __init__(self, session: Session):
        self.follow_ups = FollowUpRepository(session)
        self.patients = PatientRepository(session)
        self.visits = VisitRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    def create_follow_up(self, payload: FollowUpCreate, *, actor: QueueActor, context: AuditContext) -> FollowUpRead:
        self._ensure_clinical_actor(actor)
        self._validate_patient(payload.patient_id)
        self._validate_visit(payload.patient_id, payload.visit_id)
        self._validate_doctor(payload.doctor_id)
        self._ensure_doctor_can_write(actor, payload.doctor_id)

        follow_up = FollowUp(
            patient_id=payload.patient_id,
            visit_id=payload.visit_id,
            doctor_id=payload.doctor_id,
            due_date=payload.due_date,
            reason=payload.reason,
            notes=payload.notes,
            status=FollowUpStatus.PENDING,
        )
        follow_up = self.follow_ups.create(follow_up)
        self.audit.log_action(
            context=context,
            action="follow_up.create",
            resource_type="follow_up",
            resource_id=follow_up.id,
            metadata={"due_date": follow_up.due_date.isoformat(), "status": follow_up.status.value},
        )
        self.follow_ups.commit()
        return self._build_read(follow_up)

    def list_follow_ups(
        self,
        *,
        actor: QueueActor,
        patient_id: UUID | None,
        status_filter: FollowUpStatus | None,
        due_before: date | None,
        limit: int,
        offset: int,
    ) -> FollowUpListResponse:
        self._ensure_clinical_actor(actor)
        effective_doctor_id = self._effective_doctor_filter(actor)

        if patient_id is not None:
            self._validate_patient(patient_id)

        items, total = self.follow_ups.list(
            patient_id=patient_id,
            doctor_id=effective_doctor_id,
            status=status_filter,
            due_before=due_before,
            reference_date=self._today(),
            limit=limit,
            offset=offset,
        )
        return FollowUpListResponse(items=[self._build_read(item) for item in items], total=total)

    def update_follow_up(
        self,
        follow_up_id: UUID,
        payload: FollowUpUpdate,
        *,
        actor: QueueActor,
        context: AuditContext,
    ) -> FollowUpRead:
        self._ensure_clinical_actor(actor)
        follow_up = self._get_follow_up_or_404(follow_up_id)
        self._ensure_doctor_can_manage(actor, follow_up)

        current_status = self._current_status(follow_up)
        if current_status not in ALLOWED_ACTION_SOURCE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot update follow-up with status {current_status.value}",
            )

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(follow_up, field, value)

        self.audit.log_action(
            context=context,
            action="follow_up.update",
            resource_type="follow_up",
            resource_id=follow_up.id,
            metadata={"changed_fields": sorted(updates.keys())},
        )
        self.follow_ups.commit()
        return self._build_read(follow_up)

    def complete_follow_up(self, follow_up_id: UUID, *, actor: QueueActor, context: AuditContext) -> FollowUpRead:
        return self._transition_status(
            follow_up_id=follow_up_id,
            next_status=FollowUpStatus.COMPLETED,
            actor=actor,
            context=context,
            action="follow_up.complete",
        )

    def cancel_follow_up(self, follow_up_id: UUID, *, actor: QueueActor, context: AuditContext) -> FollowUpRead:
        return self._transition_status(
            follow_up_id=follow_up_id,
            next_status=FollowUpStatus.CANCELLED,
            actor=actor,
            context=context,
            action="follow_up.cancel",
        )

    def _transition_status(
        self,
        *,
        follow_up_id: UUID,
        next_status: FollowUpStatus,
        actor: QueueActor,
        context: AuditContext,
        action: str,
    ) -> FollowUpRead:
        self._ensure_clinical_actor(actor)
        follow_up = self._get_follow_up_or_404(follow_up_id)
        self._ensure_doctor_can_manage(actor, follow_up)

        current_status = self._current_status(follow_up)
        if current_status not in ALLOWED_ACTION_SOURCE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot change follow-up status from {current_status.value} to {next_status.value}",
            )

        follow_up.status = next_status
        self.audit.log_action(
            context=context,
            action=action,
            resource_type="follow_up",
            resource_id=follow_up.id,
            metadata={"from_status": current_status.value, "to_status": next_status.value},
        )
        self.follow_ups.commit()
        return self._build_read(follow_up)

    def _get_follow_up_or_404(self, follow_up_id: UUID) -> FollowUp:
        follow_up = self.follow_ups.get_by_id(follow_up_id)
        if follow_up is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
        return follow_up

    def _validate_patient(self, patient_id: UUID) -> None:
        patient = self.patients.get_by_id(patient_id)
        if patient is None or patient.archived_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    def _validate_visit(self, patient_id: UUID, visit_id: UUID) -> None:
        visit = self.visits.get_by_id(visit_id)
        if visit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
        if visit.patient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="visit does not belong to the provided patient",
            )

    def _validate_doctor(self, doctor_id: UUID) -> None:
        user = self.users.get_by_id(doctor_id)
        if user is None or user.role != Role.DOCTOR or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    def _build_read(self, follow_up: FollowUp) -> FollowUpRead:
        effective_status = self._current_status(follow_up)
        return FollowUpRead(
            id=follow_up.id,
            patient_id=follow_up.patient_id,
            visit_id=follow_up.visit_id,
            doctor_id=follow_up.doctor_id,
            due_date=follow_up.due_date,
            reason=follow_up.reason,
            notes=follow_up.notes,
            status=effective_status,
            created_at=follow_up.created_at,
            updated_at=follow_up.updated_at,
        )

    def _effective_doctor_filter(self, actor: QueueActor) -> UUID | None:
        if actor.role == "admin":
            return None
        if actor.user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor identity is required")
        return actor.user_id

    def _ensure_clinical_actor(self, actor: QueueActor) -> None:
        if actor.role not in {"admin", "doctor"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

    def _ensure_doctor_can_write(self, actor: QueueActor, doctor_id: UUID) -> None:
        if actor.role != "doctor":
            return
        if actor.user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor identity is required")
        if actor.user_id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors can only create follow-ups for themselves",
            )

    def _ensure_doctor_can_manage(self, actor: QueueActor, follow_up: FollowUp) -> None:
        if actor.role == "admin":
            return
        if actor.role != "doctor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        if actor.user_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor identity is required")
        if actor.user_id != follow_up.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctors can only manage their own follow-ups",
            )

    def _current_status(self, follow_up: FollowUp) -> FollowUpStatus:
        if follow_up.status == FollowUpStatus.PENDING and follow_up.due_date < self._today():
            return FollowUpStatus.OVERDUE
        return follow_up.status

    def _today(self) -> date:
        return datetime.now(UTC).date()
