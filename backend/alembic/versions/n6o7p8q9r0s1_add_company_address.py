"""add companies.address

Revision ID: n6o7p8q9r0s1
Revises: m5n6o7p8q9r0
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "n6o7p8q9r0s1"
down_revision = "m5n6o7p8q9r0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column(
            "address",
            sa.String(length=500),
            nullable=True,
            comment="기업 주소 (면접 메일의 기본 면접 장소로 사용)",
        ),
    )


def downgrade() -> None:
    op.drop_column("companies", "address")
