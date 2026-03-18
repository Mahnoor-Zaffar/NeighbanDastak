"""Add prescriptions and prescription items tables

Revision ID: 20260317_0006
Revises: 20260317_0005
Create Date: 2026-03-17 07:10:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260317_0006"
down_revision: Union[str, None] = "20260317_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prescriptions",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("doctor_id", sa.Uuid(), nullable=False),
        sa.Column("diagnosis_summary", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"], name=op.f("fk_prescriptions_doctor_id_users")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_prescriptions_patient_id_patients")),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], name=op.f("fk_prescriptions_visit_id_visits")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prescriptions")),
    )
    op.create_index(op.f("ix_prescriptions_doctor_id"), "prescriptions", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_prescriptions_patient_id"), "prescriptions", ["patient_id"], unique=False)
    op.create_index(op.f("ix_prescriptions_visit_id"), "prescriptions", ["visit_id"], unique=False)

    op.create_table(
        "prescription_items",
        sa.Column("prescription_id", sa.Uuid(), nullable=False),
        sa.Column("medicine_name", sa.String(length=120), nullable=False),
        sa.Column("dosage", sa.String(length=120), nullable=False),
        sa.Column("frequency", sa.String(length=120), nullable=False),
        sa.Column("duration", sa.String(length=120), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prescription_id"],
            ["prescriptions.id"],
            name=op.f("fk_prescription_items_prescription_id_prescriptions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prescription_items")),
    )
    op.create_index(
        op.f("ix_prescription_items_prescription_id"),
        "prescription_items",
        ["prescription_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_prescription_items_prescription_id"), table_name="prescription_items")
    op.drop_table("prescription_items")

    op.drop_index(op.f("ix_prescriptions_visit_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_patient_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_doctor_id"), table_name="prescriptions")
    op.drop_table("prescriptions")
