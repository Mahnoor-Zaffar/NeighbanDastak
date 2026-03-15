from __future__ import annotations

import re
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

RECORD_NUMBER_PATTERN = re.compile(r"^PAT-[A-Z0-9-]{1,28}$")
PHONE_PATTERN = re.compile(r"^[0-9+() -]{7,20}$")
MIN_DATE_OF_BIRTH = date(1900, 1, 1)


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


class PatientBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_number: str | None = Field(default=None, max_length=32)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("record_number")
    @classmethod
    def validate_record_number(cls, value: str | None) -> str | None:
        normalized = _normalize_optional_string(value)
        if normalized is None:
            return None

        normalized = normalized.upper()
        if not RECORD_NUMBER_PATTERN.fullmatch(normalized):
            raise ValueError("record_number must use letters, numbers, and hyphens only")

        return normalized

    @field_validator("first_name", "last_name", "city", "notes")
    @classmethod
    def normalize_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value cannot be empty")

        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        normalized = _normalize_optional_string(value)
        if normalized is None:
            return None

        if not PHONE_PATTERN.fullmatch(normalized):
            raise ValueError("phone must contain 7 to 20 digits or phone symbols")

        return normalized

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        if value < MIN_DATE_OF_BIRTH:
            raise ValueError("date_of_birth is unrealistically old")

        return value


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_number: str | None = Field(default=None, max_length=32)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("record_number")
    @classmethod
    def validate_record_number(cls, value: str | None) -> str | None:
        return PatientBase.validate_record_number(value)

    @field_validator("first_name", "last_name", "city", "notes")
    @classmethod
    def normalize_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return PatientBase.normalize_text_fields(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return PatientBase.validate_phone(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is None:
            return None

        return PatientBase.validate_date_of_birth(value)


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    email: EmailStr | None
    phone: str | None
    city: str | None
    notes: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PatientListResponse(BaseModel):
    items: list[PatientRead]
    total: int
