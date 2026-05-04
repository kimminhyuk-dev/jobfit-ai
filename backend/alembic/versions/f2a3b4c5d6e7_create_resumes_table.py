"""create resumes table

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("resume_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="이력서 PK"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="소유자 user_id"),
        sa.Column("title", sa.String(length=120), nullable=False, comment="이력서 제목"),
        sa.Column("original_filename", sa.String(length=255), nullable=False, comment="사용자가 업로드한 원본 파일명"),
        sa.Column("stored_filename", sa.String(length=255), nullable=False, comment="서버 저장 파일명"),
        sa.Column("file_path", sa.String(length=500), nullable=False, comment="서버 저장 경로"),
        sa.Column("file_size", sa.BigInteger(), nullable=False, comment="파일 크기(byte)"),
        sa.Column("content_type", sa.String(length=120), nullable=False, comment="업로드 Content-Type"),
        sa.Column("raw_text", sa.Text(), nullable=True, comment="파일에서 추출한 원문 텍스트"),
        sa.Column("parsed_data", sa.JSON(), nullable=True, comment="규칙 기반 파싱 결과 JSON"),
        sa.Column("parse_status", sa.String(length=20), server_default="PENDING", nullable=False, comment="파싱 상태: PENDING / COMPLETED / FAILED"),
        sa.Column("parse_error", sa.Text(), nullable=True, comment="파싱 실패 메시지"),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False, comment="기본 이력서 여부"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id (회원가입 시에는 null)"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, comment="삭제 여부 (소프트 삭제)"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("resume_id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_index("ix_resumes_parse_status", "resumes", ["parse_status"])


def downgrade() -> None:
    op.drop_index("ix_resumes_parse_status", table_name="resumes")
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")
