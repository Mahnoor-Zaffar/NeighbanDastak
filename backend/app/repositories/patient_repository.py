from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models.patient import Patient


class PatientRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, patient: Patient) -> Patient:
        self.session.add(patient)
        self.session.flush()
        self.session.refresh(patient)
        return patient

    def get_by_id(self, patient_id: UUID) -> Patient | None:
        statement = select(Patient).where(Patient.id == patient_id)
        return self.session.scalar(statement)

    def get_by_record_number(self, record_number: str) -> Patient | None:
        statement = select(Patient).where(Patient.record_number == record_number)
        return self.session.scalar(statement)

    def list(
        self,
        *,
        search: str | None,
        include_archived: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Patient], int]:
        statement = select(Patient)
        count_statement = select(func.count()).select_from(Patient)

        if not include_archived:
            active_filter = Patient.archived_at.is_(None)
            statement = statement.where(active_filter)
            count_statement = count_statement.where(active_filter)

        if search:
            pattern = f"%{search.strip()}%"
            search_filter = or_(
                Patient.record_number.ilike(pattern),
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.email.ilike(pattern),
                Patient.phone.ilike(pattern),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        statement = statement.order_by(Patient.last_name, Patient.first_name).offset(offset).limit(limit)

        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def commit(self) -> None:
        self.session.commit()
