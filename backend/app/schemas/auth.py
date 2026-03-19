from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.rbac import Role


class DemoDoctorProfileRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    full_name: str
    email: str
    specialty: str | None


class DemoDoctorProfileListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DemoDoctorProfileRead]
    total: int


class DemoLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    doctor_profile_id: UUID | None = None


class DemoCurrentUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    user_id: UUID | None
    doctor_profile_id: UUID | None
    full_name: str | None
    email: str | None
