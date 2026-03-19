from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.db.models.user import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.session.scalar(statement)

    def get_active_doctor_by_id(self, doctor_id: UUID) -> User | None:
        statement = select(User).where(
            User.id == doctor_id,
            User.role == Role.DOCTOR,
            User.is_active.is_(True),
        )
        return self.session.scalar(statement)

    def get_first_active_doctor(self) -> User | None:
        statement = (
            select(User)
            .where(
                User.role == Role.DOCTOR,
                User.is_active.is_(True),
            )
            .order_by(User.full_name.asc(), User.email.asc())
        )
        return self.session.scalar(statement)

    def list_active_doctors(self) -> list[User]:
        statement = (
            select(User)
            .where(
                User.role == Role.DOCTOR,
                User.is_active.is_(True),
            )
            .order_by(User.full_name.asc(), User.email.asc())
        )
        return list(self.session.scalars(statement))
