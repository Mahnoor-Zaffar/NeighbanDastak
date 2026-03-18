from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models.prescription import Prescription, PrescriptionItem


class PrescriptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, prescription: Prescription) -> Prescription:
        self.session.add(prescription)
        self.session.flush()
        self.session.refresh(prescription)
        return prescription

    def create_items(self, items: list[PrescriptionItem]) -> list[PrescriptionItem]:
        self.session.add_all(items)
        self.session.flush()
        for item in items:
            self.session.refresh(item)
        return items

    def get_by_id(self, prescription_id: UUID) -> Prescription | None:
        statement = select(Prescription).where(Prescription.id == prescription_id)
        return self.session.scalar(statement)

    def list_by_patient(
        self,
        *,
        patient_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Prescription], int]:
        statement = (
            select(Prescription)
            .where(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count()).select_from(Prescription).where(Prescription.patient_id == patient_id)
        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def list_by_visit(
        self,
        *,
        visit_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[list[Prescription], int]:
        statement = (
            select(Prescription)
            .where(Prescription.visit_id == visit_id)
            .order_by(Prescription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count()).select_from(Prescription).where(Prescription.visit_id == visit_id)
        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def list_items_by_prescription_id(self, prescription_id: UUID) -> list[PrescriptionItem]:
        statement = (
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_id == prescription_id)
            .order_by(PrescriptionItem.created_at, PrescriptionItem.id)
        )
        return list(self.session.scalars(statement))

    def list_items_by_prescription_ids(
        self,
        prescription_ids: list[UUID],
    ) -> dict[UUID, list[PrescriptionItem]]:
        if not prescription_ids:
            return {}

        statement = (
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_id.in_(prescription_ids))
            .order_by(PrescriptionItem.created_at, PrescriptionItem.id)
        )
        grouped: dict[UUID, list[PrescriptionItem]] = defaultdict(list)
        for item in self.session.scalars(statement):
            grouped[item.prescription_id].append(item)
        return grouped

    def delete_items_by_prescription_id(self, prescription_id: UUID) -> None:
        statement = delete(PrescriptionItem).where(PrescriptionItem.prescription_id == prescription_id)
        self.session.execute(statement)

    def delete(self, prescription: Prescription) -> None:
        self.session.delete(prescription)

    def commit(self) -> None:
        self.session.commit()
