from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    occurred_at: datetime
    actor_id: uuid.UUID | None
    actor_role: str
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    request_id: str | None
    ip_address: str | None
    metadata_json: dict[str, Any] | None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
