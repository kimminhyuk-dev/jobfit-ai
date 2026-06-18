"""add email verification rate limit columns

Revision ID: o7p8q9r0s1t2
Revises: n6o7p8q9r0s1
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "o7p8q9r0s1t2"
down_revision = "n6o7p8q9r0s1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_verifications",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="검증 실패 시도 횟수",
        ),
    )
    op.add_column(
        "email_verifications",
        sa.Column(
            "last_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="마지막 검증 시도 시각",
        ),
    )


def downgrade() -> None:
    op.drop_column("email_verifications", "last_attempt_at")
    op.drop_column("email_verifications", "attempt_count")
