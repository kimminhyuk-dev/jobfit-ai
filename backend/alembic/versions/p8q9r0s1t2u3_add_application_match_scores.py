"""add application match scores

Revision ID: p8q9r0s1t2u3
Revises: o7p8q9r0s1t2
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "p8q9r0s1t2u3"
down_revision = "o7p8q9r0s1t2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_match_scores",
        sa.Column(
            "match_score_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="Match score PK",
        ),
        sa.Column(
            "application_id",
            sa.BigInteger(),
            nullable=False,
            comment="Scored application id",
        ),
        sa.Column("score", sa.Integer(), nullable=False, comment="0-100 matching score"),
        sa.Column("grade", sa.String(length=2), nullable=False, comment="Matching grade A/B/C/D"),
        sa.Column(
            "summary",
            sa.Text(),
            server_default="",
            nullable=False,
            comment="Short score rationale",
        ),
        sa.Column(
            "strengths",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
            comment="Positive matching factors",
        ),
        sa.Column(
            "gaps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
            comment="Missing or weak matching factors",
        ),
        sa.Column(
            "matched_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
            comment="Skills found on both resume and job posting",
        ),
        sa.Column(
            "missing_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
            comment="Job skills not found on the resume",
        ),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Scoring component details",
        ),
        sa.Column("model", sa.String(length=80), nullable=False, comment="Scoring model or algorithm name"),
        sa.Column(
            "algorithm_version",
            sa.String(length=40),
            nullable=False,
            comment="Scoring algorithm version",
        ),
        sa.Column(
            "input_signature",
            sa.String(length=64),
            nullable=False,
            comment="SHA-256 signature of scored input fields",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_ip", sa.String(length=45), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_ip", sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.application_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("match_score_id"),
        sa.UniqueConstraint("application_id", name="uq_application_match_scores_application_id"),
    )
    op.create_index(
        op.f("ix_application_match_scores_application_id"),
        "application_match_scores",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_match_scores_input_signature"),
        "application_match_scores",
        ["input_signature"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_match_scores_input_signature"),
        table_name="application_match_scores",
    )
    op.drop_index(
        op.f("ix_application_match_scores_application_id"),
        table_name="application_match_scores",
    )
    op.drop_table("application_match_scores")
