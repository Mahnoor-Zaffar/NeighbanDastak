from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class Prescription(BaseModel):
    __tablename__ = "prescriptions"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    visit_id: Mapped[UUID] = mapped_column(ForeignKey("visits.id"), nullable=False, index=True)
    doctor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    diagnosis_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PrescriptionItem(BaseModel):
    __tablename__ = "prescription_items"

    prescription_id: Mapped[UUID] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    medicine_name: Mapped[str] = mapped_column(String(120), nullable=False)
    dosage: Mapped[str] = mapped_column(String(120), nullable=False)
    frequency: Mapped[str] = mapped_column(String(120), nullable=False)
    duration: Mapped[str] = mapped_column(String(120), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
