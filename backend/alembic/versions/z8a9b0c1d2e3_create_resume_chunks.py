"""create resume chunks

Revision ID: z8a9b0c1d2e3
Revises: y7z8a9b0c1d2
Create Date: 2026-06-24
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "z8a9b0c1d2e3"
down_revision = "y7z8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resume_chunks",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
            comment="이력서 청크 PK",
        ),
        sa.Column(
            "resume_id",
            sa.BigInteger(),
            nullable=False,
            comment="부모 이력서 PK",
        ),
        sa.Column(
            "section",
            sa.String(length=80),
            nullable=False,
            comment="청크 섹션 라벨",
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
            comment="이력서 내 청크 순번",
        ),
        sa.Column("content", sa.Text(), nullable=False, comment="청크 텍스트"),
        sa.Column(
            "embedding",
            Vector(1536),
            nullable=False,
            comment="text-embedding-3-small 1536차원 임베딩",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="생성 시각",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="최종 수정 시각",
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column(
            "updated_ip",
            sa.String(length=45),
            nullable=True,
            comment="최종 수정 요청 IP",
        ),
        sa.Column("reg_user_id", sa.BigInteger(), nullable=True, comment="생성한 user_id"),
        sa.Column("reg_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column(
            "reg_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="생성 일시",
        ),
        sa.Column("mod_user_id", sa.BigInteger(), nullable=True, comment="마지막 수정 user_id"),
        sa.Column("mod_ip", sa.String(length=45), nullable=True, comment="마지막 수정 요청 IP"),
        sa.Column(
            "mod_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="마지막 수정 일시",
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resume_id",
            "chunk_index",
            name="uq_resume_chunks_resume_id_chunk_index",
        ),
    )
    op.create_index("ix_resume_chunks_resume_id", "resume_chunks", ["resume_id"])
    op.execute(
        "CREATE INDEX ix_resume_chunks_embedding_hnsw "
        "ON resume_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_resume_chunks_embedding_hnsw")
    op.drop_index("ix_resume_chunks_resume_id", table_name="resume_chunks")
    op.drop_table("resume_chunks")
