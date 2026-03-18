"""Add follow-ups table for internal reminder tracking

Revision ID: 20260317_0008
Revises: 20260317_0007
Create Date: 2026-03-17 12:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260317_0008"
down_revision: Union[str, None] = "20260317_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "follow_ups",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("visit_id", sa.Uuid(), nullable=False),
        sa.Column("doctor_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "completed",
                "cancelled",
                "overdue",
                name="follow_up_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"], name=op.f("fk_follow_ups_doctor_id_users")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], name=op.f("fk_follow_ups_patient_id_patients")),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], name=op.f("fk_follow_ups_visit_id_visits")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_follow_ups")),
    )
    op.create_index(op.f("ix_follow_ups_patient_id"), "follow_ups", ["patient_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_visit_id"), "follow_ups", ["visit_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_doctor_id"), "follow_ups", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_due_date"), "follow_ups", ["due_date"], unique=False)
    op.create_index(op.f("ix_follow_ups_status"), "follow_ups", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_follow_ups_status"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_due_date"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_doctor_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_visit_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_patient_id"), table_name="follow_ups")
    op.drop_table("follow_ups")
