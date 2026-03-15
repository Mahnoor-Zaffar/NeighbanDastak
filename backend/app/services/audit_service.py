from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository

MAX_METADATA_VALUE_LENGTH = 120


@dataclass(slots=True)
class AuditContext:
    actor_role: str
    request_id: str | None
    ip_address: str | None


class AuditService:
    def __init__(self, session: Session):
        self.repository = AuditLogRepository(session)

    def log_action(
        self,
        *,
        context: AuditContext,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        log = AuditLog(
            actor_role=context.actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=context.request_id,
            ip_address=context.ip_address,
            metadata_json=self._sanitize_metadata(metadata),
        )
        self.repository.create(log)

    def _sanitize_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if metadata is None:
            return None

        sanitized: dict[str, Any] = {}
        for key, value in metadata.items():
            if isinstance(value, str):
                sanitized[key] = value[:MAX_METADATA_VALUE_LENGTH]
                continue

            if isinstance(value, (int, float, bool)) or value is None:
                sanitized[key] = value
                continue

            if isinstance(value, list):
                sanitized[key] = [self._sanitize_scalar(item) for item in value][:20]
                continue

            sanitized[key] = str(value)[:MAX_METADATA_VALUE_LENGTH]

        return sanitized

    def _sanitize_scalar(self, value: Any) -> str | int | float | bool | None:
        if isinstance(value, str):
            return value[:MAX_METADATA_VALUE_LENGTH]
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        return str(value)[:MAX_METADATA_VALUE_LENGTH]
