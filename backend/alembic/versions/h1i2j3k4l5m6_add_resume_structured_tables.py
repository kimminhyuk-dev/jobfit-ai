"""add resume_projects and resume_cover_letter_sections tables

Revision ID: h1i2j3k4l5m6
Revises: a1b2c3d4e5f6
Create Date: 2026-05-06

이력서 프로젝트와 자기소개서 목차를 JSON 블롭 대신
정규화된 테이블로 저장해 쿼리 가능성과 타입 안전성을 확보한다.
"""

from alembic import op
import sqlalchemy as sa

revision = "h1i2j3k4l5m6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- resume_projects ---
    op.create_table(
        "resume_projects",
        sa.Column("project_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="프로젝트 PK"),
        sa.Column("resume_id", sa.BigInteger(), nullable=False, comment="부모 이력서 PK"),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False, comment="표시 순서"),
        sa.Column("name", sa.String(200), nullable=True, comment="프로젝트명"),
        sa.Column("period", sa.String(100), nullable=True, comment="수행 기간"),
        sa.Column("role", sa.Text(), nullable=True, comment="맡은 역할"),
        sa.Column("description", sa.Text(), nullable=True, comment="프로젝트 내용"),
        sa.Column("review", sa.Text(), nullable=True, comment="후기·배운 점"),
        sa.Column("tech_stack", sa.JSON(), nullable=True, comment="사용 기술 목록"),
        sa.Column("raw_text", sa.Text(), nullable=True, comment="원문 블록"),
        # AuditMixin columns
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(45), nullable=True, comment="최종 수정 요청 IP"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_index("ix_resume_projects_resume_id", "resume_projects", ["resume_id"])

    # --- resume_cover_letter_sections ---
    op.create_table(
        "resume_cover_letter_sections",
        sa.Column("section_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="자기소개서 목차 PK"),
        sa.Column("resume_id", sa.BigInteger(), nullable=False, comment="부모 이력서 PK"),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False, comment="표시 순서"),
        sa.Column("title", sa.String(200), nullable=False, comment="소제목"),
        sa.Column("content", sa.Text(), server_default="", nullable=False, comment="내용"),
        # AuditMixin columns
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(45), nullable=True, comment="최종 수정 요청 IP"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("section_id"),
    )
    op.create_index("ix_resume_cover_letter_sections_resume_id", "resume_cover_letter_sections", ["resume_id"])


def downgrade() -> None:
    op.drop_index("ix_resume_cover_letter_sections_resume_id", table_name="resume_cover_letter_sections")
    op.drop_table("resume_cover_letter_sections")
    op.drop_index("ix_resume_projects_resume_id", table_name="resume_projects")
    op.drop_table("resume_projects")
