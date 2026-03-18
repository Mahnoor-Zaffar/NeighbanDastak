from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class FollowUpStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class FollowUp(BaseModel):
    __tablename__ = "follow_ups"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    visit_id: Mapped[UUID] = mapped_column(ForeignKey("visits.id"), nullable=False, index=True)
    doctor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus, name="follow_up_status", native_enum=False),
        nullable=False,
        default=FollowUpStatus.PENDING,
        index=True,
    )
