from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import CurrentActor, QueueActor, get_queue_actor, require_roles
from app.core.rbac import Role
from app.db.session import get_db_session
from app.schemas.patient import PatientCreate, PatientListResponse, PatientRead, PatientUpdate
from app.schemas.timeline import PatientTimelineResponse
from app.services.audit_service import AuditContext
from app.services.patient_service import PatientService
from app.services.patient_timeline_service import PatientTimelineService

router = APIRouter(prefix="/patients", tags=["patients"])

ReadActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN, Role.DOCTOR, Role.RECEPTIONIST))]
AdminActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN))]
TimelineActor = Annotated[QueueActor, Depends(get_queue_actor)]


def get_patient_service(session: Annotated[Session, Depends(get_db_session)]) -> PatientService:
    return PatientService(session)


def get_patient_timeline_service(session: Annotated[Session, Depends(get_db_session)]) -> PatientTimelineService:
    return PatientTimelineService(session)


@router.get("", response_model=PatientListResponse)
def list_patients(
    _: ReadActor,
    service: Annotated[PatientService, Depends(get_patient_service)],
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    include_archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PatientListResponse:
    return service.list_patients(
        search=q,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    actor: AdminActor,
    request: Request,
    payload: PatientCreate,
    service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientRead:
    return service.create_patient(
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.get("/{patient_id}/timeline", response_model=PatientTimelineResponse)
def get_patient_timeline(
    actor: TimelineActor,
    patient_id: UUID,
    service: Annotated[PatientTimelineService, Depends(get_patient_timeline_service)],
) -> PatientTimelineResponse:
    return service.get_timeline(patient_id, actor=actor)


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    _: ReadActor,
    patient_id: UUID,
    service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientRead:
    return service.get_patient(patient_id)


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(
    actor: AdminActor,
    request: Request,
    patient_id: UUID,
    payload: PatientUpdate,
    service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientRead:
    return service.update_patient(
        patient_id,
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.delete("/{patient_id}", response_model=PatientRead)
def archive_patient(
    actor: AdminActor,
    request: Request,
    patient_id: UUID,
    service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientRead:
    return service.archive_patient(
        patient_id,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )
