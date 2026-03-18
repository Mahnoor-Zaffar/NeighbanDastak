from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.follow_up import FollowUpStatus


def _normalize_required_string(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("value cannot be empty")
    return normalized


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class FollowUpCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    visit_id: UUID
    doctor_id: UUID
    due_date: date
    reason: str = Field(max_length=255)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return _normalize_required_string(value)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class FollowUpUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    due_date: date | None = None
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_required_string(value)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class FollowUpRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    visit_id: UUID
    doctor_id: UUID
    due_date: date
    reason: str
    notes: str | None
    status: FollowUpStatus
    created_at: datetime
    updated_at: datetime


class FollowUpListResponse(BaseModel):
    items: list[FollowUpRead]
    total: int
