"""Add patients table

Revision ID: 20260315_0002
Revises: 20260315_0001
Create Date: 2026-03-15 00:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260315_0002"
down_revision: Union[str, None] = "20260315_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("record_number", sa.String(length=32), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patients")),
        sa.UniqueConstraint("record_number", name=op.f("uq_patients_record_number")),
    )
    op.create_index(op.f("ix_patients_archived_at"), "patients", ["archived_at"], unique=False)
    op.create_index(op.f("ix_patients_record_number"), "patients", ["record_number"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_patients_record_number"), table_name="patients")
    op.drop_index(op.f("ix_patients_archived_at"), table_name="patients")
    op.drop_table("patients")
