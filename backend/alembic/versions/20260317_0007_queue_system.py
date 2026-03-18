"""Add appointment queue fields for smart queue MVP

Revision ID: 20260317_0007
Revises: 20260317_0006
Create Date: 2026-03-17 10:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260317_0007"
down_revision: Union[str, None] = "20260317_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("scheduled_date", sa.Date(), nullable=True))
    op.add_column("appointments", sa.Column("queue_number", sa.Integer(), nullable=True))
    op.add_column(
        "appointments",
        sa.Column(
            "queue_status",
            sa.Enum(
                "waiting",
                "in_progress",
                "completed",
                "skipped",
                name="appointment_queue_status",
                native_enum=False,
            ),
            nullable=True,
        ),
    )
    op.add_column("appointments", sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("called_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("assigned_doctor_id", sa.Uuid(), nullable=True))

    appointments = sa.table(
        "appointments",
        sa.column("scheduled_for", sa.DateTime(timezone=True)),
        sa.column("scheduled_date", sa.Date()),
    )
    op.execute(
        appointments.update().values(
            {
                "scheduled_date": sa.cast(appointments.c.scheduled_for, sa.Date()),
            }
        )
    )

    op.alter_column("appointments", "scheduled_date", nullable=False)
    op.create_foreign_key(
        op.f("fk_appointments_assigned_doctor_id_users"),
        "appointments",
        "users",
        ["assigned_doctor_id"],
        ["id"],
    )

    op.create_index(op.f("ix_appointments_scheduled_date"), "appointments", ["scheduled_date"], unique=False)
    op.create_index(op.f("ix_appointments_queue_number"), "appointments", ["queue_number"], unique=False)
    op.create_index(op.f("ix_appointments_queue_status"), "appointments", ["queue_status"], unique=False)
    op.create_index(op.f("ix_appointments_checked_in_at"), "appointments", ["checked_in_at"], unique=False)
    op.create_index(op.f("ix_appointments_called_at"), "appointments", ["called_at"], unique=False)
    op.create_index(op.f("ix_appointments_completed_at"), "appointments", ["completed_at"], unique=False)
    op.create_index(op.f("ix_appointments_assigned_doctor_id"), "appointments", ["assigned_doctor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_appointments_assigned_doctor_id"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_completed_at"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_called_at"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_checked_in_at"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_queue_status"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_queue_number"), table_name="appointments")
    op.drop_index(op.f("ix_appointments_scheduled_date"), table_name="appointments")

    op.drop_constraint(op.f("fk_appointments_assigned_doctor_id_users"), "appointments", type_="foreignkey")
    op.drop_column("appointments", "assigned_doctor_id")
    op.drop_column("appointments", "completed_at")
    op.drop_column("appointments", "called_at")
    op.drop_column("appointments", "checked_in_at")
    op.drop_column("appointments", "queue_status")
    op.drop_column("appointments", "queue_number")
    op.drop_column("appointments", "scheduled_date")
