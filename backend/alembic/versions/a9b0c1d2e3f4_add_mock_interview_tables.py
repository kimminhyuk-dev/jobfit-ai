"""add mock interview tables

Revision ID: a9b0c1d2e3f4
Revises: z8a9b0c1d2e3
Create Date: 2026-06-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a9b0c1d2e3f4"
down_revision = "z8a9b0c1d2e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mock_interview_sessions",
        sa.Column("session_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="IN_PROGRESS",
            nullable=False,
        ),
        sa.Column(
            "stage",
            sa.String(length=20),
            server_default="WARMUP",
            nullable=False,
        ),
        sa.Column("question_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_ip", sa.String(length=45), nullable=True),
        sa.Column("reg_user_id", sa.BigInteger(), nullable=True),
        sa.Column("reg_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "reg_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("mod_user_id", sa.BigInteger(), nullable=True),
        sa.Column("mod_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "mod_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.job_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        op.f("ix_mock_interview_sessions_job_id"),
        "mock_interview_sessions",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mock_interview_sessions_resume_id"),
        "mock_interview_sessions",
        ["resume_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mock_interview_sessions_stage"),
        "mock_interview_sessions",
        ["stage"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mock_interview_sessions_status"),
        "mock_interview_sessions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mock_interview_sessions_user_id"),
        "mock_interview_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "mock_interview_turns",
        sa.Column("turn_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("based_on_chunk", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_ip", sa.String(length=45), nullable=True),
        sa.Column("reg_user_id", sa.BigInteger(), nullable=True),
        sa.Column("reg_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "reg_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("mod_user_id", sa.BigInteger(), nullable=True),
        sa.Column("mod_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "mod_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["mock_interview_sessions.session_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("turn_id"),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_mock_interview_turn_order"),
    )
    op.create_index(
        op.f("ix_mock_interview_turns_session_id"),
        "mock_interview_turns",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mock_interview_turns_stage"),
        "mock_interview_turns",
        ["stage"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mock_interview_turns_stage"), table_name="mock_interview_turns")
    op.drop_index(
        op.f("ix_mock_interview_turns_session_id"),
        table_name="mock_interview_turns",
    )
    op.drop_table("mock_interview_turns")
    op.drop_index(
        op.f("ix_mock_interview_sessions_user_id"),
        table_name="mock_interview_sessions",
    )
    op.drop_index(
        op.f("ix_mock_interview_sessions_status"),
        table_name="mock_interview_sessions",
    )
    op.drop_index(
        op.f("ix_mock_interview_sessions_stage"),
        table_name="mock_interview_sessions",
    )
    op.drop_index(
        op.f("ix_mock_interview_sessions_resume_id"),
        table_name="mock_interview_sessions",
    )
    op.drop_index(
        op.f("ix_mock_interview_sessions_job_id"),
        table_name="mock_interview_sessions",
    )
    op.drop_table("mock_interview_sessions")
