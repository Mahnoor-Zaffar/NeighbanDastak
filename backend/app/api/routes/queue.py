from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor, get_queue_actor
from app.db.session import get_db_session
from app.schemas.queue import QueueCheckInRequest, QueueEntryRead, QueueListResponse
from app.services.audit_service import AuditContext
from app.services.queue_service import QueueService

router = APIRouter(tags=["queue"])

QueueActorDependency = Annotated[QueueActor, Depends(get_queue_actor)]


def get_queue_service(session: Annotated[Session, Depends(get_db_session)]) -> QueueService:
    return QueueService(session)


@router.post("/appointments/{appointment_id}/check-in", response_model=QueueEntryRead)
def check_in_appointment(
    actor: QueueActorDependency,
    request: Request,
    appointment_id: UUID,
    service: Annotated[QueueService, Depends(get_queue_service)],
    payload: Annotated[QueueCheckInRequest | None, Body()] = None,
) -> QueueEntryRead:
    return service.check_in(
        appointment_id,
        payload or QueueCheckInRequest(),
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.get("/queue", response_model=QueueListResponse)
def list_queue(
    actor: QueueActorDependency,
    service: Annotated[QueueService, Depends(get_queue_service)],
    scheduled_date: date = Query(default_factory=date.today),
    include_history: bool = False,
) -> QueueListResponse:
    return service.list_queue(
        actor=actor,
        scheduled_date=scheduled_date,
        doctor_id=None,
        include_history=include_history,
    )


@router.get("/queue/doctor/{doctor_id}", response_model=QueueListResponse)
def list_queue_by_doctor(
    actor: QueueActorDependency,
    doctor_id: UUID,
    service: Annotated[QueueService, Depends(get_queue_service)],
    scheduled_date: date = Query(default_factory=date.today),
    include_history: bool = False,
) -> QueueListResponse:
    return service.list_queue(
        actor=actor,
        scheduled_date=scheduled_date,
        doctor_id=doctor_id,
        include_history=include_history,
    )


@router.post("/queue/{appointment_id}/call", response_model=QueueEntryRead)
def call_queue_entry(
    actor: QueueActorDependency,
    request: Request,
    appointment_id: UUID,
    service: Annotated[QueueService, Depends(get_queue_service)],
) -> QueueEntryRead:
    return service.call_next(
        appointment_id,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.post("/queue/{appointment_id}/complete", response_model=QueueEntryRead)
def complete_queue_entry(
    actor: QueueActorDependency,
    request: Request,
    appointment_id: UUID,
    service: Annotated[QueueService, Depends(get_queue_service)],
) -> QueueEntryRead:
    return service.complete(
        appointment_id,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.post("/queue/{appointment_id}/skip", response_model=QueueEntryRead)
def skip_queue_entry(
    actor: QueueActorDependency,
    request: Request,
    appointment_id: UUID,
    service: Annotated[QueueService, Depends(get_queue_service)],
) -> QueueEntryRead:
    return service.skip(
        appointment_id,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )
