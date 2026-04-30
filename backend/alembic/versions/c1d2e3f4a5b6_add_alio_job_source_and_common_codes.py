"""add alio job source and common codes

Revision ID: c1d2e3f4a5b6
Revises: b9a9c0967b9a
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b9a9c0967b9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "common_code_groups",
        sa.Column("group_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("category_code", sa.String(length=30), nullable=False),
        sa.Column("code_group", sa.String(length=30), nullable=False),
        sa.Column("code_group_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.PrimaryKeyConstraint("group_id"),
        sa.UniqueConstraint(
            "category_code",
            "code_group",
            name="uq_common_code_groups_category_group",
        ),
        sa.UniqueConstraint("code_group", name="uq_common_code_groups_code_group"),
    )
    op.create_index(
        op.f("ix_common_code_groups_category_code"),
        "common_code_groups",
        ["category_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_common_code_groups_code_group"),
        "common_code_groups",
        ["code_group"],
        unique=False,
    )

    op.create_table(
        "common_codes",
        sa.Column("code_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code_group", sa.String(length=30), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("code_name", sa.String(length=200), nullable=False),
        sa.Column("code_description", sa.Text(), nullable=True),
        sa.Column("parent_code", sa.String(length=50), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.ForeignKeyConstraint(["code_group"], ["common_code_groups.code_group"]),
        sa.PrimaryKeyConstraint("code_id"),
        sa.UniqueConstraint("code_group", "code", name="uq_common_codes_group_code"),
    )
    op.create_index(
        op.f("ix_common_codes_code"), "common_codes", ["code"], unique=False
    )
    op.create_index(
        op.f("ix_common_codes_code_group"),
        "common_codes",
        ["code_group"],
        unique=False,
    )
    op.create_index(
        op.f("ix_common_codes_parent_code"),
        "common_codes",
        ["parent_code"],
        unique=False,
    )

    op.add_column(
        "batch_job_runs",
        sa.Column("source", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "batch_job_runs",
        sa.Column("success_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index(
        op.f("ix_batch_job_runs_source"),
        "batch_job_runs",
        ["source"],
        unique=False,
    )

    op.add_column(
        "job_postings",
        sa.Column("location_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("career_level_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("education_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("ncs_category", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("ncs_category_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("organization_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("organization_type_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("organization_category", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("organization_category_code", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("ministry", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("ministry_code", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("updated_from_source_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_job_postings_location_code"),
        "job_postings",
        ["location_code"],
        unique=False,
    )

    _seed_common_code_groups()
    _seed_common_codes()


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_job_postings_location_code"), table_name="job_postings")
    op.drop_column("job_postings", "updated_from_source_at")
    op.drop_column("job_postings", "ministry_code")
    op.drop_column("job_postings", "ministry")
    op.drop_column("job_postings", "organization_category_code")
    op.drop_column("job_postings", "organization_category")
    op.drop_column("job_postings", "organization_type_code")
    op.drop_column("job_postings", "organization_type")
    op.drop_column("job_postings", "ncs_category_code")
    op.drop_column("job_postings", "ncs_category")
    op.drop_column("job_postings", "education_code")
    op.drop_column("job_postings", "career_level_code")
    op.drop_column("job_postings", "location_code")

    op.drop_index(op.f("ix_batch_job_runs_source"), table_name="batch_job_runs")
    op.drop_column("batch_job_runs", "success_count")
    op.drop_column("batch_job_runs", "source")

    op.drop_index(op.f("ix_common_codes_parent_code"), table_name="common_codes")
    op.drop_index(op.f("ix_common_codes_code_group"), table_name="common_codes")
    op.drop_index(op.f("ix_common_codes_code"), table_name="common_codes")
    op.drop_table("common_codes")
    op.drop_index(
        op.f("ix_common_code_groups_code_group"), table_name="common_code_groups"
    )
    op.drop_index(
        op.f("ix_common_code_groups_category_code"), table_name="common_code_groups"
    )
    op.drop_table("common_code_groups")


def _seed_common_code_groups() -> None:
    group_table = sa.table(
        "common_code_groups",
        sa.column("category_code", sa.String),
        sa.column("code_group", sa.String),
        sa.column("code_group_name", sa.String),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(
        group_table,
        [
            _group("REC", "R1000", "고용형태"),
            _group("REC", "R2000", "채용구분"),
            _group("REC", "R3000", "근무지"),
            _group("REC", "R6000", "NCS분류"),
            _group("REC", "R7000", "학력정보"),
            _group("REC", "ATCH_TYPE", "첨부유형"),
            _group("INST", "A2000", "기관유형"),
            _group("INST", "INST_CLSF", "기관분류"),
            _group("INST", "A1000", "주무부처"),
        ],
    )


def _seed_common_codes() -> None:
    code_table = sa.table(
        "common_codes",
        sa.column("code_group", sa.String),
        sa.column("code", sa.String),
        sa.column("code_name", sa.String),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        code_table,
        [
            _code("R1000", "R1010", "정규직", 10),
            _code("R1000", "R1020", "계약직", 20),
            _code("R2000", "R2010", "신입", 10),
            _code("R2000", "R2020", "경력", 20),
            _code("R3000", "R3010", "서울", 10),
            _code("R3000", "R3017", "경기", 17),
            _code("R7000", "R7040", "대졸(2~3년)", 40),
            _code("A2000", "A2005", "기타공공기관", 50),
        ],
    )


def _group(category_code: str, code_group: str, name: str) -> dict[str, str]:
    return {
        "category_code": category_code,
        "code_group": code_group,
        "code_group_name": name,
        "description": f"ALIO {name} 코드 그룹",
    }


def _code(
    code_group: str,
    code: str,
    code_name: str,
    sort_order: int,
) -> dict[str, str | int]:
    return {
        "code_group": code_group,
        "code": code,
        "code_name": code_name,
        "sort_order": sort_order,
    }
