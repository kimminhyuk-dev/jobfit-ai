"""add audit logs and reg/mod audit columns

Revision ID: w5x6y7z8a9b0
Revises: v4w5x6y7z8a9
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "w5x6y7z8a9b0"
down_revision = "v4w5x6y7z8a9"
branch_labels = None
depends_on = None


AUDIT_TARGET_TABLES = (
    "user_roles",
    "leave_balances",
    "admin_leave_requests",
)


def upgrade() -> None:
    for table_name in AUDIT_TARGET_TABLES:
        _add_reg_mod_columns(table_name)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="감사 로그 PK"),
        sa.Column("table_name", sa.String(length=80), nullable=False, comment="변경 대상 테이블"),
        sa.Column("record_id", sa.String(length=100), nullable=False, comment="변경 대상 레코드 식별값"),
        sa.Column("action", sa.String(length=20), nullable=False, comment="행위: CREATE/UPDATE/DELETE"),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True, comment="행위자 user_id"),
        sa.Column("actor_ip", sa.String(length=45), nullable=True, comment="행위자 IP"),
        sa.Column(
            "before_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="변경 전 값",
        ),
        sa.Column(
            "after_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="변경 후 값",
        ),
        sa.Column("summary", sa.String(length=255), nullable=True, comment="변경 요약"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment="기록 일시",
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_table_name", "audit_logs", ["table_name"])
    op.create_index("ix_audit_logs_record_id", "audit_logs", ["record_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO permissions (code, name, description) "
            "VALUES ('AUDIT_VIEW', '감사 로그 조회', '관리자 감사 로그 조회 권한') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    bind.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.role_id, p.permission_id "
            "FROM roles r, permissions p "
            "WHERE r.code = 'SUPER_ADMIN' AND p.code = 'AUDIT_VIEW' "
            "ON CONFLICT (role_id, permission_id) DO NOTHING"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN ("
            "SELECT permission_id FROM permissions WHERE code = 'AUDIT_VIEW'"
            ")"
        )
    )
    bind.execute(sa.text("DELETE FROM permissions WHERE code = 'AUDIT_VIEW'"))

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_record_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_table_name", table_name="audit_logs")
    op.drop_table("audit_logs")

    for table_name in reversed(AUDIT_TARGET_TABLES):
        _drop_reg_mod_columns(table_name)


def _add_reg_mod_columns(table_name: str) -> None:
    op.add_column(table_name, sa.Column("reg_user_id", sa.BigInteger(), nullable=True, comment="생성한 user_id"))
    op.add_column(table_name, sa.Column("reg_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"))
    op.add_column(
        table_name,
        sa.Column(
            "reg_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="생성 일시",
        ),
    )
    op.add_column(table_name, sa.Column("mod_user_id", sa.BigInteger(), nullable=True, comment="마지막 수정 user_id"))
    op.add_column(table_name, sa.Column("mod_ip", sa.String(length=45), nullable=True, comment="마지막 수정 요청 IP"))
    op.add_column(
        table_name,
        sa.Column(
            "mod_dt",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
            comment="마지막 수정 일시",
        ),
    )


def _drop_reg_mod_columns(table_name: str) -> None:
    op.drop_column(table_name, "mod_dt")
    op.drop_column(table_name, "mod_ip")
    op.drop_column(table_name, "mod_user_id")
    op.drop_column(table_name, "reg_dt")
    op.drop_column(table_name, "reg_ip")
    op.drop_column(table_name, "reg_user_id")
