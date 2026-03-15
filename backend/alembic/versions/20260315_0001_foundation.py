"""Initialize backend foundation baseline

Revision ID: 20260315_0001
Revises:
Create Date: 2026-03-15 00:00:00
"""

from typing import Sequence, Union

revision: str = "20260315_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
