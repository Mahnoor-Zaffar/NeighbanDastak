from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class VisitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    appointment_id: UUID | None = None
    started_at: datetime
    ended_at: datetime | None = None
    complaint: str | None = Field(default=None, max_length=255)
    diagnosis_summary: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("started_at")
    @classmethod
    def validate_started_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("started_at must include timezone information")

        return value

    @field_validator("ended_at")
    @classmethod
    def validate_ended_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("ended_at must include timezone information")

        return value

    @field_validator("complaint", "diagnosis_summary", "notes")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)

    @model_validator(mode="after")
    def validate_time_window(self) -> "VisitCreate":
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at cannot be before started_at")

        return self


class VisitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    appointment_id: UUID | None
    started_at: datetime
    ended_at: datetime | None
    complaint: str | None
    diagnosis_summary: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class VisitListResponse(BaseModel):
    items: list[VisitRead]
    total: int


class VisitUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime | None = None
    ended_at: datetime | None = None
    complaint: str | None = Field(default=None, max_length=255)
    diagnosis_summary: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_timestamps(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("timestamps must include timezone information")
        return value

    @field_validator("complaint", "diagnosis_summary", "notes")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)

    @model_validator(mode="after")
    def validate_time_window(self) -> "VisitUpdate":
        if self.started_at is not None and self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at cannot be before started_at")
        return self
