"""Add actor_id to audit_logs

Revision ID: 20260319_0009
Revises: 20260317_0008
Create Date: 2026-03-19 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260319_0009"
down_revision: Union[str, None] = "20260317_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("actor_id", sa.Uuid(), nullable=True),
    )
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_actor_id"), table_name="audit_logs")
    op.drop_column("audit_logs", "actor_id")
