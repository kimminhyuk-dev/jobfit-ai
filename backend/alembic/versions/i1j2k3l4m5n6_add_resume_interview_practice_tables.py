"""add resume interview practice tables

Revision ID: i1j2k3l4m5n6
Revises: h1i2j3k4l5m6
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "i1j2k3l4m5n6"
down_revision = "h1i2j3k4l5m6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resume_interview_sessions",
        sa.Column("session_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="Interview session PK"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="Owner user_id"),
        sa.Column("resume_id", sa.BigInteger(), nullable=False, comment="Source resume_id"),
        sa.Column("status", sa.String(length=20), server_default="IN_PROGRESS", nullable=False, comment="IN_PROGRESS / COMPLETED"),
        sa.Column("model", sa.String(length=80), nullable=False, comment="OpenAI model used for question generation"),
        sa.Column("total_score", sa.Integer(), nullable=True, comment="Sum of submitted answer scores"),
        sa.Column("max_score", sa.Integer(), server_default="100", nullable=False, comment="Maximum session score"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Created at"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="Created by user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="Created request IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Updated at"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="Updated by user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="Updated request IP"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_resume_interview_sessions_resume_id", "resume_interview_sessions", ["resume_id"])
    op.create_index("ix_resume_interview_sessions_status", "resume_interview_sessions", ["status"])
    op.create_index("ix_resume_interview_sessions_user_id", "resume_interview_sessions", ["user_id"])

    op.create_table(
        "resume_interview_questions",
        sa.Column("question_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="Interview question PK"),
        sa.Column("session_id", sa.BigInteger(), nullable=False, comment="Parent interview session"),
        sa.Column("display_order", sa.Integer(), nullable=False, comment="Display order from 1 to 5"),
        sa.Column("question", sa.Text(), nullable=False, comment="Interview question text"),
        sa.Column("question_type", sa.String(length=30), nullable=False, comment="Question type"),
        sa.Column("source", sa.String(length=30), nullable=False, comment="Question source category"),
        sa.Column("intent", sa.Text(), nullable=False, comment="Question intent"),
        sa.Column("difficulty", sa.String(length=30), nullable=False, comment="Question difficulty"),
        sa.Column("expected_keywords", sa.JSON(), nullable=True, comment="Expected answer keywords"),
        sa.Column("official_references", sa.JSON(), nullable=True, comment="Allowed official references for this question"),
        sa.Column("max_score", sa.Integer(), server_default="20", nullable=False, comment="Maximum question score"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Created at"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="Created by user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="Created request IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Updated at"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="Updated by user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="Updated request IP"),
        sa.ForeignKeyConstraint(["session_id"], ["resume_interview_sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id"),
    )
    op.create_index("ix_resume_interview_questions_question_type", "resume_interview_questions", ["question_type"])
    op.create_index("ix_resume_interview_questions_session_id", "resume_interview_questions", ["session_id"])

    op.create_table(
        "resume_interview_answers",
        sa.Column("answer_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="Interview answer PK"),
        sa.Column("question_id", sa.BigInteger(), nullable=False, comment="Answered question"),
        sa.Column("user_answer", sa.Text(), nullable=False, comment="Submitted user answer"),
        sa.Column("score", sa.Integer(), nullable=False, comment="Evaluated score"),
        sa.Column("max_score", sa.Integer(), server_default="20", nullable=False, comment="Maximum answer score"),
        sa.Column("verdict", sa.String(length=20), nullable=False, comment="GOOD / PARTIAL / INSUFFICIENT / UNKNOWN"),
        sa.Column("strengths", sa.JSON(), nullable=True, comment="Correct or strong answer points"),
        sa.Column("missing_points", sa.JSON(), nullable=True, comment="Missing answer points"),
        sa.Column("incorrect_points", sa.JSON(), nullable=True, comment="Incorrect answer points"),
        sa.Column("feedback", sa.Text(), nullable=False, comment="Actionable feedback"),
        sa.Column("reference_based_answer", sa.Text(), nullable=False, comment="Reference-based improved answer"),
        sa.Column("official_references_used", sa.JSON(), nullable=True, comment="Official references used in evaluation"),
        sa.Column("model", sa.String(length=80), nullable=False, comment="OpenAI model used for answer evaluation"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Created at"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="Created by user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="Created request IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="Updated at"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="Updated by user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="Updated request IP"),
        sa.ForeignKeyConstraint(["question_id"], ["resume_interview_questions.question_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("answer_id"),
        sa.UniqueConstraint("question_id"),
    )
    op.create_index("ix_resume_interview_answers_question_id", "resume_interview_answers", ["question_id"])
    op.create_index("ix_resume_interview_answers_verdict", "resume_interview_answers", ["verdict"])


def downgrade() -> None:
    op.drop_index("ix_resume_interview_answers_verdict", table_name="resume_interview_answers")
    op.drop_index("ix_resume_interview_answers_question_id", table_name="resume_interview_answers")
    op.drop_table("resume_interview_answers")
    op.drop_index("ix_resume_interview_questions_session_id", table_name="resume_interview_questions")
    op.drop_index("ix_resume_interview_questions_question_type", table_name="resume_interview_questions")
    op.drop_table("resume_interview_questions")
    op.drop_index("ix_resume_interview_sessions_user_id", table_name="resume_interview_sessions")
    op.drop_index("ix_resume_interview_sessions_status", table_name="resume_interview_sessions")
    op.drop_index("ix_resume_interview_sessions_resume_id", table_name="resume_interview_sessions")
    op.drop_table("resume_interview_sessions")
