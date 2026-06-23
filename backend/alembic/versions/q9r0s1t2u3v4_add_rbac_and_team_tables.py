"""add rbac and team tables

RBAC(역할 기반 접근 제어) + 조직(팀) 구조 스키마.
- roles / permissions / role_permissions / user_roles (NIST 표준 다대다)
- teams + users.team_id / users.team_role (휴가 결재선 계산용)

데이터 시드/백필은 다음 마이그레이션(r0s1t2u3v4w5)에서 수행한다(DDL/DML 분리).

Revision ID: q9r0s1t2u3v4
Revises: p8q9r0s1t2u3
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "q9r0s1t2u3v4"
down_revision = "p8q9r0s1t2u3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── teams ──────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("team_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="팀 PK"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="팀 이름"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="팀 설명"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="활성 여부"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, comment="삭제 여부"),
        sa.PrimaryKeyConstraint("team_id"),
    )

    # ── roles ──────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("role_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="역할 PK"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="역할 코드 (예: SUPER_ADMIN)"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="역할 표시명"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="역할 설명"),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="활성 여부"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.PrimaryKeyConstraint("role_id"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    op.create_index("ix_roles_code", "roles", ["code"])

    # ── permissions ────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="권한 PK"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="권한 코드 (예: LEAVE_APPROVE)"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="권한 표시명"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="권한 설명"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.PrimaryKeyConstraint("permission_id"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])

    # ── role_permissions (역할-권한 다대다) ─────────────────
    op.create_table(
        "role_permissions",
        sa.Column("role_permission_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="역할-권한 매핑 PK"),
        sa.Column("role_id", sa.BigInteger(), nullable=False, comment="역할 role_id"),
        sa.Column("permission_id", sa.BigInteger(), nullable=False, comment="권한 permission_id"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.permission_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_permission_id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    # ── user_roles (사용자-역할 다대다) ─────────────────────
    op.create_table(
        "user_roles",
        sa.Column("user_role_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="사용자-역할 매핑 PK"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="사용자 user_id"),
        sa.Column("role_id", sa.BigInteger(), nullable=False, comment="역할 role_id"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="부여 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="역할을 부여한 user_id (백필/시드는 null)"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_role_id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    # ── users.team_id / users.team_role ────────────────────
    op.add_column(
        "users",
        sa.Column("team_id", sa.BigInteger(), nullable=True, comment="소속 팀 team_id (결재선 계산용)"),
    )
    op.add_column(
        "users",
        sa.Column("team_role", sa.String(length=10), nullable=True, comment="팀 내 역할: LEAD / MEMBER"),
    )
    op.create_index("ix_users_team_id", "users", ["team_id"])
    op.create_foreign_key(
        "fk_users_team_id",
        "users",
        "teams",
        ["team_id"],
        ["team_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_team_id", "users", type_="foreignkey")
    op.drop_index("ix_users_team_id", table_name="users")
    op.drop_column("users", "team_role")
    op.drop_column("users", "team_id")

    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_roles_code", table_name="roles")
    op.drop_table("roles")

    op.drop_table("teams")
