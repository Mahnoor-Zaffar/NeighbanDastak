from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        return log

    def list(
        self,
        *,
        actor_role: str | None,
        actor_id: uuid.UUID | None,
        action: str | None,
        resource_type: str | None,
        resource_id: uuid.UUID | None,
        occurred_after: datetime | None,
        occurred_before: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        statement = select(AuditLog)
        count_statement = select(func.count()).select_from(AuditLog)
        filters = []

        if actor_role is not None:
            filters.append(AuditLog.actor_role == actor_role)
        if actor_id is not None:
            filters.append(AuditLog.actor_id == actor_id)
        if action is not None:
            filters.append(AuditLog.action == action)
        if resource_type is not None:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditLog.resource_id == resource_id)
        if occurred_after is not None:
            filters.append(AuditLog.occurred_at >= occurred_after)
        if occurred_before is not None:
            filters.append(AuditLog.occurred_at <= occurred_before)

        if filters:
            where_clause = and_(*filters)
            statement = statement.where(where_clause)
            count_statement = count_statement.where(where_clause)

        statement = statement.order_by(AuditLog.occurred_at.desc()).offset(offset).limit(limit)

        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total
