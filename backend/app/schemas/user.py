from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.rbac import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    specialty: str | None
    license_number: str | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
