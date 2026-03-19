from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps.permissions import CurrentActor, require_roles
from app.core.rbac import Role
from app.db.session import get_db_session
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogListResponse, AuditLogRead

router = APIRouter(prefix="/audit-logs", tags=["audit"])

AdminActor = Annotated[CurrentActor, Depends(require_roles(Role.ADMIN))]


def get_audit_log_repository(session: Annotated[Session, Depends(get_db_session)]) -> AuditLogRepository:
    return AuditLogRepository(session)


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    _: AdminActor,
    repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    actor_role: str | None = None,
    actor_id: UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    occurred_after: datetime | None = None,
    occurred_before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditLogListResponse:
    items, total = repository.list(
        actor_role=actor_role,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        occurred_after=occurred_after,
        occurred_before=occurred_before,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=[AuditLogRead.model_validate(item) for item in items],
        total=total,
    )
