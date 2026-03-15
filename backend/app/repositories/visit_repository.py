from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
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

    def commit(self) -> None:
        self.session.commit()
