"""add email_verifications table

Revision ID: m5n6o7p8q9r0
Revises: l4m5n6o7p8q9
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa


revision = "m5n6o7p8q9r0"
down_revision = "l4m5n6o7p8q9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False, comment="인증 대상 이메일"),
        sa.Column(
            "purpose",
            sa.String(length=30),
            server_default="PASSWORD_RESET",
            nullable=False,
            comment="용도: PASSWORD_RESET / SIGNUP 등",
        ),
        sa.Column(
            "code_hash",
            sa.String(length=64),
            nullable=False,
            comment="인증 코드의 SHA-256 해시 (평문 미저장)",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="만료 시각",
        ),
        sa.Column(
            "is_used",
            sa.Boolean(),
            server_default="false",
            nullable=False,
            comment="사용(소비) 여부",
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="사용 처리 시각",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="발급 시각",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_verifications_email", "email_verifications", ["email"]
    )
    op.create_index(
        "ix_email_verifications_code_hash", "email_verifications", ["code_hash"]
    )


def downgrade() -> None:
    op.drop_index("ix_email_verifications_code_hash", table_name="email_verifications")
    op.drop_index("ix_email_verifications_email", table_name="email_verifications")
    op.drop_table("email_verifications")
