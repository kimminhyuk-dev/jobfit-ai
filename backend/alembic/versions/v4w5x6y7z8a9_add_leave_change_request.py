"""add change-request columns to admin leave requests

Revision ID: v4w5x6y7z8a9
Revises: u3v4w5x6y7z8
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "v4w5x6y7z8a9"
down_revision = "u3v4w5x6y7z8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admin_leave_requests",
        sa.Column(
            "change_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="일정 변경 요청 시각",
        ),
    )
    op.add_column(
        "admin_leave_requests",
        sa.Column(
            "change_request_reason",
            sa.String(length=1000),
            nullable=True,
            comment="일정 변경 요청 사유",
        ),
    )


def downgrade() -> None:
    op.drop_column("admin_leave_requests", "change_request_reason")
    op.drop_column("admin_leave_requests", "change_requested_at")
