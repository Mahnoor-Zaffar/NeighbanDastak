from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import CurrentActor, QueueActor, get_queue_actor, require_roles
from app.core.rbac import Role
from app.db.models.appointment import AppointmentStatus
from app.db.session import get_db_session
from app.schemas.appointment import AppointmentCreate, AppointmentListResponse, AppointmentRead, AppointmentUpdate
from app.services.audit_service import AuditContext
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["appointments"])

ReadActor = Annotated[QueueActor, Depends(get_queue_actor)]
AllowedActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN, Role.DOCTOR))]
AdminActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN))]


def get_appointment_service(session: Annotated[Session, Depends(get_db_session)]) -> AppointmentService:
    return AppointmentService(session)


@router.get("", response_model=AppointmentListResponse)
def list_appointments(
    _: ReadActor,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    patient_id: UUID | None = None,
    status_filter: Annotated[AppointmentStatus | None, Query(alias="status")] = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AppointmentListResponse:
    return service.list_appointments(
        patient_id=patient_id,
        status=status_filter,
        starts_at=starts_at,
        ends_at=ends_at,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(
    actor: AllowedActor,
    request: Request,
    payload: AppointmentCreate,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> AppointmentRead:
    return service.create_appointment(
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(
    _: ReadActor,
    appointment_id: UUID,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> AppointmentRead:
    return service.get_appointment(appointment_id)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
def update_appointment(
    actor: AllowedActor,
    request: Request,
    appointment_id: UUID,
    payload: AppointmentUpdate,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> AppointmentRead:
    if actor.role == Role.DOCTOR and payload.patient_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors cannot reassign appointments to a different patient",
        )

    return service.update_appointment(
        appointment_id,
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(
    actor: AdminActor,
    request: Request,
    appointment_id: UUID,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> Response:
    service.delete_appointment(
        appointment_id,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
