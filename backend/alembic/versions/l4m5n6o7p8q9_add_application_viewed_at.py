"""add viewed_at column to applications

Revision ID: l4m5n6o7p8q9
Revises: k3l4m5n6o7p8
Create Date: 2026-06-16
"""

from alembic import op
import sqlalchemy as sa


revision = "l4m5n6o7p8q9"
down_revision = "k3l4m5n6o7p8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "applications",
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="기업이 이력서를 처음 열람한 시각 (미열람이면 null)",
        ),
    )


def downgrade() -> None:
    op.drop_column("applications", "viewed_at")
