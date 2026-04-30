"""add job_sources table

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


WORK24_DISABLED_REASON = (
    "WORK24 채용정보 API는 일반 사용자 제한으로 현재 사용할 수 없는 수집원입니다."
)


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "batch_job_runs",
        "status",
        existing_type=sa.String(length=20),
        comment="READY/RUNNING/SUCCESS/PARTIAL_SUCCESS/FAILED/BLOCKED/SKIPPED/RATE_LIMITED",
        existing_nullable=False,
    )

    op.create_table(
        "job_sources",
        sa.Column("source_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_code", sa.String(length=20), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("disabled_reason", sa.Text(), nullable=True),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_ip", sa.String(length=45), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("source_code"),
    )
    op.create_index(
        op.f("ix_job_sources_source_code"),
        "job_sources",
        ["source_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_job_sources_status"),
        "job_sources",
        ["status"],
        unique=False,
    )

    source_table = sa.table(
        "job_sources",
        sa.column("source_code", sa.String),
        sa.column("source_name", sa.String),
        sa.column("status", sa.String),
        sa.column("disabled_reason", sa.Text),
        sa.column("base_url", sa.String),
    )
    op.bulk_insert(
        source_table,
        [
            {
                "source_code": "ALIO",
                "source_name": "ALIO 공공기관 채용정보",
                "status": "ACTIVE",
                "disabled_reason": None,
                "base_url": "https://opendata.alio.go.kr",
            },
            {
                "source_code": "WORK24",
                "source_name": "Work24/고용24 채용정보",
                "status": "PENDING_APPROVAL",
                "disabled_reason": WORK24_DISABLED_REASON,
                "base_url": "https://www.work24.go.kr",
            },
            {
                "source_code": "SARAMIN",
                "source_name": "사람인 채용정보",
                "status": "DISABLED",
                "disabled_reason": "사람인 수집원은 아직 구현되지 않았습니다.",
                "base_url": None,
            },
            {
                "source_code": "MANUAL",
                "source_name": "관리자 수동 등록",
                "status": "ACTIVE",
                "disabled_reason": None,
                "base_url": None,
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_job_sources_status"), table_name="job_sources")
    op.drop_index(op.f("ix_job_sources_source_code"), table_name="job_sources")
    op.drop_table("job_sources")
    op.alter_column(
        "batch_job_runs",
        "status",
        existing_type=sa.String(length=20),
        comment="READY/RUNNING/SUCCESS/FAILED/PARTIAL_SUCCESS/SKIPPED/RATE_LIMITED",
        existing_nullable=False,
    )
