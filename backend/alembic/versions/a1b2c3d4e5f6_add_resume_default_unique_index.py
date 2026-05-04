"""add resume default unique index

Revision ID: a1b2c3d4e5f6
Revises: f2a3b4c5d6e7
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_resumes_one_default_per_user",
        "resumes",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default IS TRUE AND is_deleted IS FALSE"),
    )


def downgrade() -> None:
    op.drop_index("uq_resumes_one_default_per_user", table_name="resumes")
