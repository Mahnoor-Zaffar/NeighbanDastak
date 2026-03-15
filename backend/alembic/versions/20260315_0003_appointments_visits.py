"""Add appointments and visits tables

Revision ID: 20260315_0003
Revises: 20260315_0002
Create Date: 2026-03-15 01:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260315_0003"
down_revision: Union[str, None] = "20260315_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "completed",
                "cancelled",
                "no_show",
                name="appointment_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_appointments_patient_id_patients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointments")),
    )
    op.create_index(op.f("ix_appointments_patient_id"), "appointments", ["patient_id"], unique=False)
    op.create_index(op.f("ix_appointments_scheduled_for"), "appointments", ["scheduled_for"], unique=False)

    op.create_table(
        "visits",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("appointment_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("complaint", sa.String(length=255), nullable=True),
        sa.Column("diagnosis_summary", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], name=op.f("fk_visits_appointment_id_appointments")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_visits_patient_id_patients")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visits")),
        sa.UniqueConstraint("appointment_id", name=op.f("uq_visits_appointment_id")),
    )
    op.create_index(op.f("ix_visits_appointment_id"), "visits", ["appointment_id"], unique=True)
    op.create_index(op.f("ix_visits_patient_id"), "visits", ["patient_id"], unique=False)
    op.create_index(op.f("ix_visits_started_at"), "visits", ["started_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_visits_started_at"), table_name="visits")
    op.drop_index(op.f("ix_visits_patient_id"), table_name="visits")
    op.drop_index(op.f("ix_visits_appointment_id"), table_name="visits")
    op.drop_table("visits")
    op.drop_index(op.f("ix_appointments_scheduled_for"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_patient_id"), table_name="appointments")
    op.drop_table("appointments")
