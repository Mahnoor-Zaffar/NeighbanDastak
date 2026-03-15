from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps.permissions import CurrentActor, require_roles
from app.core.rbac import Role
from app.db.session import get_db_session
from app.schemas.visit import VisitCreate, VisitRead, VisitUpdate
from app.services.audit_service import AuditContext
from app.services.visit_service import VisitService

router = APIRouter(prefix="/visits", tags=["visits"])

AllowedActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN, Role.DOCTOR))]


def get_visit_service(session: Annotated[Session, Depends(get_db_session)]) -> VisitService:
    return VisitService(session)


@router.post("", response_model=VisitRead, status_code=status.HTTP_201_CREATED)
def create_visit(
    actor: AllowedActor,
    request: Request,
    payload: VisitCreate,
    service: Annotated[VisitService, Depends(get_visit_service)],
) -> VisitRead:
    return service.create_visit(
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )


@router.get("/{visit_id}", response_model=VisitRead)
def get_visit(
    _: AllowedActor,
    visit_id: UUID,
    service: Annotated[VisitService, Depends(get_visit_service)],
) -> VisitRead:
    return service.get_visit(visit_id)


@router.patch("/{visit_id}", response_model=VisitRead)
def update_visit(
    actor: AllowedActor,
    request: Request,
    visit_id: UUID,
    payload: VisitUpdate,
    service: Annotated[VisitService, Depends(get_visit_service)],
) -> VisitRead:
    return service.update_visit(
        visit_id,
        payload,
        context=AuditContext(
            actor_role=actor.role.value,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
        ),
    )
