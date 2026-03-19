from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
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

    def list(
        self,
        *,
        role: Role | None,
        is_active: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[User], int]:
        statement = select(User)
        count_statement = select(func.count()).select_from(User)
        filters = []

        if role is not None:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active.is_(is_active))

        if filters:
            from sqlalchemy import and_
            where_clause = and_(*filters)
            statement = statement.where(where_clause)
            count_statement = count_statement.where(where_clause)

        statement = statement.order_by(User.full_name.asc(), User.email.asc()).offset(offset).limit(limit)
        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def commit(self) -> None:
        self.session.commit()
