"""pgvector 확장 켜기

Revision ID: y7z8a9b0c1d2
Revises: x6y7z8a9b0c1
Create Date: 2026-06-24
"""

from alembic import op


revision = "y7z8a9b0c1d2"
down_revision = "x6y7z8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """vector 타입을 쓸 수 있도록 pgvector 확장을 켠다."""

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """이번 단계에서 켠 pgvector 확장을 끈다."""

    op.execute("DROP EXTENSION IF EXISTS vector")
