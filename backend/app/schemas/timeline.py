from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PatientTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    event_type: str
    event_timestamp: datetime
    title: str
    subtitle: str | None
    actor_name: str | None
    related_entity_type: str
    related_entity_id: str
    metadata: dict[str, Any]


class PatientTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str
    sort_order: str
    items: list[PatientTimelineEvent]
    total: int
