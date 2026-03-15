from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.appointment import AppointmentStatus


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    scheduled_for: datetime
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_for(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("scheduled_for must include timezone information")

        return value

    @field_validator("reason", "notes")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class AppointmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID | None = None
    scheduled_for: datetime | None = None
    status: AppointmentStatus | None = None
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("scheduled_for")
    @classmethod
    def validate_scheduled_for(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("scheduled_for must include timezone information")

        return value

    @field_validator("reason", "notes")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    scheduled_for: datetime
    status: AppointmentStatus
    reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AppointmentListResponse(BaseModel):
    items: list[AppointmentRead]
    total: int
