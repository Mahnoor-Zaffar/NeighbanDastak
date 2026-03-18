from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db.models.follow_up import FollowUp, FollowUpStatus


class FollowUpRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, follow_up: FollowUp) -> FollowUp:
        self.session.add(follow_up)
        self.session.flush()
        self.session.refresh(follow_up)
        return follow_up

    def get_by_id(self, follow_up_id: UUID) -> FollowUp | None:
        statement = select(FollowUp).where(FollowUp.id == follow_up_id)
        return self.session.scalar(statement)

    def list(
        self,
        *,
        patient_id: UUID | None,
        doctor_id: UUID | None,
        status: FollowUpStatus | None,
        due_before: date | None,
        reference_date: date,
        limit: int,
        offset: int,
    ) -> tuple[list[FollowUp], int]:
        statement = select(FollowUp)
        count_statement = select(func.count()).select_from(FollowUp)

        filters = self._build_filters(
            patient_id=patient_id,
            doctor_id=doctor_id,
            status=status,
            due_before=due_before,
            reference_date=reference_date,
        )
        if filters:
            where_clause = and_(*filters)
            statement = statement.where(where_clause)
            count_statement = count_statement.where(where_clause)

        statement = statement.order_by(FollowUp.due_date.asc(), FollowUp.created_at.desc()).offset(offset).limit(limit)

        items = list(self.session.scalars(statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def commit(self) -> None:
        self.session.commit()

    def _build_filters(
        self,
        *,
        patient_id: UUID | None,
        doctor_id: UUID | None,
        status: FollowUpStatus | None,
        due_before: date | None,
        reference_date: date,
    ) -> list:
        filters: list = []

        if patient_id is not None:
            filters.append(FollowUp.patient_id == patient_id)
        if doctor_id is not None:
            filters.append(FollowUp.doctor_id == doctor_id)
        if due_before is not None:
            filters.append(FollowUp.due_date <= due_before)

        if status is None:
            return filters

        if status == FollowUpStatus.OVERDUE:
            filters.append(
                or_(
                    FollowUp.status == FollowUpStatus.OVERDUE,
                    and_(FollowUp.status == FollowUpStatus.PENDING, FollowUp.due_date < reference_date),
                )
            )
            return filters

        if status == FollowUpStatus.PENDING:
            filters.append(FollowUp.status == FollowUpStatus.PENDING)
            filters.append(FollowUp.due_date >= reference_date)
            return filters

        filters.append(FollowUp.status == status)
        return filters
