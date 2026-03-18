from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import QueueActor, get_queue_actor
from app.db.models.follow_up import FollowUpStatus
from app.db.session import get_db_session
from app.schemas.follow_up import FollowUpCreate, FollowUpListResponse, FollowUpRead, FollowUpUpdate
from app.services.audit_service import AuditContext
from app.services.follow_up_service import FollowUpService

router = APIRouter(tags=["follow_ups"])

ClinicalActor = Annotated[QueueActor, Depends(get_queue_actor)]


def get_follow_up_service(session: Annotated[Session, Depends(get_db_session)]) -> FollowUpService:
    return FollowUpService(session)


@router.post("/follow-ups", response_model=FollowUpRead, status_code=status.HTTP_201_CREATED)
def create_follow_up(
    actor: ClinicalActor,
    request: Request,
    payload: FollowUpCreate,
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpRead:
    return service.create_follow_up(
        payload,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.get("/follow-ups", response_model=FollowUpListResponse)
def list_follow_ups(
    actor: ClinicalActor,
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
    status_filter: Annotated[FollowUpStatus | None, Query(alias="status")] = None,
    due_before: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FollowUpListResponse:
    return service.list_follow_ups(
        actor=actor,
        patient_id=None,
        status_filter=status_filter,
        due_before=due_before,
        limit=limit,
        offset=offset,
    )


@router.get("/patients/{patient_id}/follow-ups", response_model=FollowUpListResponse)
def list_patient_follow_ups(
    actor: ClinicalActor,
    patient_id: UUID,
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
    status_filter: Annotated[FollowUpStatus | None, Query(alias="status")] = None,
    due_before: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FollowUpListResponse:
    return service.list_follow_ups(
        actor=actor,
        patient_id=patient_id,
        status_filter=status_filter,
        due_before=due_before,
        limit=limit,
        offset=offset,
    )


@router.put("/follow-ups/{follow_up_id}", response_model=FollowUpRead)
def update_follow_up(
    actor: ClinicalActor,
    request: Request,
    follow_up_id: UUID,
    payload: FollowUpUpdate,
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpRead:
    return service.update_follow_up(
        follow_up_id,
        payload,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.post("/follow-ups/{follow_up_id}/complete", response_model=FollowUpRead)
def complete_follow_up(
    actor: ClinicalActor,
    request: Request,
    follow_up_id: UUID,
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpRead:
    return service.complete_follow_up(
        follow_up_id,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.post("/follow-ups/{follow_up_id}/cancel", response_model=FollowUpRead)
def cancel_follow_up(
    actor: ClinicalActor,
    request: Request,
    follow_up_id: UUID,
    service: Annotated[FollowUpService, Depends(get_follow_up_service)],
) -> FollowUpRead:
    return service.cancel_follow_up(
        follow_up_id,
        actor=actor,
        context=AuditContext(
            actor_role=actor.role,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )
