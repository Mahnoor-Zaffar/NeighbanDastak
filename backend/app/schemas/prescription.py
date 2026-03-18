from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _normalize_required_string(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


class PrescriptionItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medicine_name: str = Field(min_length=1, max_length=120)
    dosage: str = Field(min_length=1, max_length=120)
    frequency: str = Field(min_length=1, max_length=120)
    duration: str = Field(min_length=1, max_length=120)
    instructions: str | None = Field(default=None, max_length=1000)

    @field_validator("medicine_name")
    @classmethod
    def validate_medicine_name(cls, value: str) -> str:
        return _normalize_required_string(value, field_name="medicine_name")

    @field_validator("dosage", "frequency", "duration")
    @classmethod
    def validate_required_fields(cls, value: str, info: ValidationInfo) -> str:
        return _normalize_required_string(value, field_name=info.field_name)

    @field_validator("instructions")
    @classmethod
    def normalize_instructions(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class PrescriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    visit_id: UUID
    doctor_id: UUID
    diagnosis_summary: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    items: list[PrescriptionItemInput] = Field(min_length=1, max_length=30)

    @field_validator("diagnosis_summary")
    @classmethod
    def validate_diagnosis_summary(cls, value: str) -> str:
        return _normalize_required_string(value, field_name="diagnosis_summary")

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class PrescriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnosis_summary: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    items: list[PrescriptionItemInput] = Field(min_length=1, max_length=30)

    @field_validator("diagnosis_summary")
    @classmethod
    def validate_diagnosis_summary(cls, value: str) -> str:
        return _normalize_required_string(value, field_name="diagnosis_summary")

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)


class PrescriptionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prescription_id: UUID
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None
    created_at: datetime
    updated_at: datetime


class PrescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    visit_id: UUID
    doctor_id: UUID
    diagnosis_summary: str
    notes: str | None
    items: list[PrescriptionItemRead]
    created_at: datetime
    updated_at: datetime


class PrescriptionListResponse(BaseModel):
    items: list[PrescriptionRead]
    total: int
