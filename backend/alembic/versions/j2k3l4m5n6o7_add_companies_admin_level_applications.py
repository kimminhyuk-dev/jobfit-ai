"""add companies, users.admin_level, applications

Revision ID: j2k3l4m5n6o7
Revises: i1j2k3l4m5n6
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision = "j2k3l4m5n6o7"
down_revision = "i1j2k3l4m5n6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users.admin_level (ADMIN 등급 A/B/C)
    op.add_column(
        "users",
        sa.Column(
            "admin_level",
            sa.String(length=1),
            nullable=True,
            comment="관리자 등급 (ADMIN 전용): A / B / C",
        ),
    )

    # companies (기업회원 계정)
    op.create_table(
        "companies",
        sa.Column("company_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="기업 PK"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="로그인 계정 user_id (role=COMPANY)"),
        sa.Column("company_name", sa.String(length=200), nullable=True, comment="회사명"),
        sa.Column("business_number", sa.String(length=20), nullable=True, comment="사업자등록번호"),
        sa.Column("dedup_key", sa.String(length=220), nullable=False, comment="회사 식별 키 (bn:{사업자번호} 우선, 없으면 nm:{회사명})"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, comment="삭제 여부"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("company_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_companies_user_id", "companies", ["user_id"])
    op.create_index("ix_companies_company_name", "companies", ["company_name"])
    op.create_index("ix_companies_business_number", "companies", ["business_number"])
    op.create_index(
        "uq_companies_dedup_key",
        "companies",
        ["dedup_key"],
        unique=True,
        postgresql_where=sa.text("is_deleted IS FALSE"),
    )

    # applications (지원/이력서 보내기)
    op.create_table(
        "applications",
        sa.Column("application_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="지원 PK"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="지원자 user_id"),
        sa.Column("resume_id", sa.BigInteger(), nullable=False, comment="지원에 사용한 이력서 resume_id"),
        sa.Column("job_id", sa.BigInteger(), nullable=False, comment="지원한 공고 job_id"),
        sa.Column("company_id", sa.BigInteger(), nullable=True, comment="지원이 전달되는 기업계정 company_id"),
        sa.Column("status", sa.String(length=20), server_default="SUBMITTED", nullable=False, comment="지원 상태: SUBMITTED / VIEWED / ACCEPTED / REJECTED"),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="지원 시각"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, comment="삭제 여부"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.job_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.company_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("application_id"),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_resume_id", "applications", ["resume_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_company_id", "applications", ["company_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_applied_at", "applications", ["applied_at"])
    op.create_index(
        "uq_applications_user_job",
        "applications",
        ["user_id", "job_id"],
        unique=True,
        postgresql_where=sa.text("is_deleted IS FALSE"),
    )


def downgrade() -> None:
    op.drop_index("uq_applications_user_job", table_name="applications")
    op.drop_index("ix_applications_applied_at", table_name="applications")
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_company_id", table_name="applications")
    op.drop_index("ix_applications_job_id", table_name="applications")
    op.drop_index("ix_applications_resume_id", table_name="applications")
    op.drop_index("ix_applications_user_id", table_name="applications")
    op.drop_table("applications")

    op.drop_index("uq_companies_dedup_key", table_name="companies")
    op.drop_index("ix_companies_business_number", table_name="companies")
    op.drop_index("ix_companies_company_name", table_name="companies")
    op.drop_index("ix_companies_user_id", table_name="companies")
    op.drop_table("companies")

    op.drop_column("users", "admin_level")
