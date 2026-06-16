"""add user profile fields (birth_date, phone, gender, address, tech_stack)

Revision ID: k3l4m5n6o7p8
Revises: j2k3l4m5n6o7
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision = "k3l4m5n6o7p8"
down_revision = "j2k3l4m5n6o7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True, comment="생년월일"))
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True, comment="전화번호 (010-1234-5678 형식 정규화 저장)"))
    op.add_column("users", sa.Column("gender", sa.String(length=10), nullable=True, comment="성별: MALE / FEMALE"))
    op.add_column("users", sa.Column("zipcode", sa.String(length=10), nullable=True, comment="우편번호 (5자리, 주소검색 API)"))
    op.add_column("users", sa.Column("address1", sa.String(length=255), nullable=True, comment="기본주소 (주소검색 API 자동입력)"))
    op.add_column("users", sa.Column("address2", sa.String(length=255), nullable=True, comment="상세주소 (사용자 입력)"))
    op.add_column("users", sa.Column("tech_stack", sa.JSON(), nullable=True, comment="기술스택 문자열 배열"))


def downgrade() -> None:
    op.drop_column("users", "tech_stack")
    op.drop_column("users", "address2")
    op.drop_column("users", "address1")
    op.drop_column("users", "zipcode")
    op.drop_column("users", "gender")
    op.drop_column("users", "phone")
    op.drop_column("users", "birth_date")
