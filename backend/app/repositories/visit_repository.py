from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.models.visit import Visit


class VisitRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, visit: Visit) -> Visit:
        self.session.add(visit)
        self.session.flush()
        self.session.refresh(visit)
        return visit

    def get_by_id(self, visit_id: UUID) -> Visit | None:
        statement = select(Visit).where(Visit.id == visit_id)
        return self.session.scalar(statement)

    def get_by_appointment_id(self, appointment_id: UUID) -> Visit | None:
        statement = select(Visit).where(Visit.appointment_id == appointment_id)
        return self.session.scalar(statement)

    def list(
        self,
        *,
        patient_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Visit], int]:
        statement = select(Visit)
        count_statement = select(func.count()).select_from(Visit)
        filters = []

        if patient_id is not None:
            filters.append(Visit.patient_id == patient_id)

        if filters:
            where_clause = and_(*filters)
            statement = statement.where(where_clause)
            count_statement = count_statement.where(where_clause)

        statement = statement.order_by(Visit.started_at.desc()).offset(offset).limit(limit)
        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def commit(self) -> None:
        self.session.commit()
