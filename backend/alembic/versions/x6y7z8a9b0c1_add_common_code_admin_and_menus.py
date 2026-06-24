"""add common code admin and dynamic menus

Revision ID: x6y7z8a9b0c1
Revises: w5x6y7z8a9b0
Create Date: 2026-06-24
"""

from alembic import op
import sqlalchemy as sa


revision = "x6y7z8a9b0c1"
down_revision = "w5x6y7z8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _add_reg_mod_columns("common_code_groups")
    _add_reg_mod_columns("common_codes")

    op.add_column(
        "common_code_groups",
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="정렬 순서",
        ),
    )
    op.add_column(
        "common_code_groups",
        sa.Column(
            "use_yn",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="사용 여부",
        ),
    )
    op.add_column(
        "common_codes",
        sa.Column(
            "use_yn",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="사용 여부",
        ),
    )
    op.add_column("common_codes", sa.Column("attr1", sa.String(length=255), nullable=True, comment="여분 속성 1"))
    op.add_column("common_codes", sa.Column("attr2", sa.String(length=255), nullable=True, comment="여분 속성 2"))

    bind = op.get_bind()
    bind.execute(sa.text("UPDATE common_code_groups SET use_yn = is_active"))
    bind.execute(sa.text("UPDATE common_codes SET use_yn = is_active"))

    op.create_table(
        "menus",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="메뉴 PK"),
        sa.Column("parent_id", sa.BigInteger(), nullable=True, comment="상위 메뉴 ID"),
        sa.Column("menu_name", sa.String(length=100), nullable=False, comment="메뉴명"),
        sa.Column("menu_url", sa.String(length=255), nullable=True, comment="메뉴 URL"),
        sa.Column("icon", sa.String(length=50), nullable=True, comment="아이콘 이름"),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False, comment="정렬 순서"),
        sa.Column("use_yn", sa.Boolean(), server_default="true", nullable=False, comment="사용 여부"),
        sa.Column("required_permission", sa.String(length=50), nullable=True, comment="노출 필요 권한 코드"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, comment="삭제 여부"),
        sa.Column("reg_user_id", sa.BigInteger(), nullable=True, comment="생성한 user_id"),
        sa.Column("reg_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("reg_dt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True, comment="생성 일시"),
        sa.Column("mod_user_id", sa.BigInteger(), nullable=True, comment="마지막 수정 user_id"),
        sa.Column("mod_ip", sa.String(length=45), nullable=True, comment="마지막 수정 요청 IP"),
        sa.Column("mod_dt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True, comment="마지막 수정 일시"),
        sa.ForeignKeyConstraint(["parent_id"], ["menus.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["required_permission"], ["permissions.code"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_menus_parent_id", "menus", ["parent_id"])
    op.create_index("ix_menus_required_permission", "menus", ["required_permission"])

    _seed_permissions()
    _seed_common_codes()
    _seed_menus()


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM common_codes "
            "WHERE code_group IN ('ADMIN_POSITION', 'ADMIN_STATUS')"
        )
    )
    bind.execute(
        sa.text(
            "DELETE FROM common_code_groups "
            "WHERE code_group IN ('ADMIN_POSITION', 'ADMIN_STATUS')"
        )
    )
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions "
            "WHERE permission_id IN ("
            "SELECT permission_id FROM permissions "
            "WHERE code IN ('CODE_MANAGE', 'MENU_MANAGE')"
            ")"
        )
    )
    bind.execute(sa.text("DELETE FROM permissions WHERE code IN ('CODE_MANAGE', 'MENU_MANAGE')"))

    op.drop_index("ix_menus_required_permission", table_name="menus")
    op.drop_index("ix_menus_parent_id", table_name="menus")
    op.drop_table("menus")

    op.drop_column("common_codes", "attr2")
    op.drop_column("common_codes", "attr1")
    op.drop_column("common_codes", "use_yn")
    op.drop_column("common_code_groups", "use_yn")
    op.drop_column("common_code_groups", "sort_order")

    _drop_reg_mod_columns("common_codes")
    _drop_reg_mod_columns("common_code_groups")


def _add_reg_mod_columns(table_name: str) -> None:
    op.add_column(table_name, sa.Column("reg_user_id", sa.BigInteger(), nullable=True, comment="생성한 user_id"))
    op.add_column(table_name, sa.Column("reg_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"))
    op.add_column(table_name, sa.Column("reg_dt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True, comment="생성 일시"))
    op.add_column(table_name, sa.Column("mod_user_id", sa.BigInteger(), nullable=True, comment="마지막 수정 user_id"))
    op.add_column(table_name, sa.Column("mod_ip", sa.String(length=45), nullable=True, comment="마지막 수정 요청 IP"))
    op.add_column(table_name, sa.Column("mod_dt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True, comment="마지막 수정 일시"))


def _drop_reg_mod_columns(table_name: str) -> None:
    op.drop_column(table_name, "mod_dt")
    op.drop_column(table_name, "mod_ip")
    op.drop_column(table_name, "mod_user_id")
    op.drop_column(table_name, "reg_dt")
    op.drop_column(table_name, "reg_ip")
    op.drop_column(table_name, "reg_user_id")


def _seed_permissions() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO permissions (code, name, description) VALUES "
            "('CODE_MANAGE', '공통코드 관리', '관리자 공통코드 관리 권한'), "
            "('MENU_MANAGE', '메뉴 관리', '관리자 동적 메뉴 관리 권한') "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    bind.execute(
        sa.text(
            "INSERT INTO role_permissions (role_id, permission_id) "
            "SELECT r.role_id, p.permission_id "
            "FROM roles r, permissions p "
            "WHERE r.code = 'SUPER_ADMIN' "
            "AND p.code IN ('CODE_MANAGE', 'MENU_MANAGE') "
            "ON CONFLICT (role_id, permission_id) DO NOTHING"
        )
    )


def _seed_common_codes() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO common_code_groups "
            "(category_code, code_group, code_group_name, description, sort_order, use_yn, is_active) VALUES "
            "('ADM', 'ADMIN_POSITION', '관리자 직급', '관리자 데모 직급 코드', 10, true, true), "
            "('ADM', 'ADMIN_STATUS', '관리자 상태', '관리자 데모 상태 코드', 20, true, true) "
            "ON CONFLICT (code_group) DO NOTHING"
        )
    )
    bind.execute(
        sa.text(
            "INSERT INTO common_codes "
            "(code_group, code, code_name, sort_order, use_yn, is_active) VALUES "
            "('ADMIN_POSITION', 'LEAD', '팀장', 10, true, true), "
            "('ADMIN_POSITION', 'STAFF', '담당자', 20, true, true), "
            "('ADMIN_STATUS', 'ACTIVE', '활성', 10, true, true), "
            "('ADMIN_STATUS', 'INACTIVE', '비활성', 20, true, true) "
            "ON CONFLICT (code_group, code) DO NOTHING"
        )
    )


def _seed_menus() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO menus "
            "(menu_name, menu_url, icon, sort_order, use_yn, required_permission) VALUES "
            "('공통코드 관리', '/admin/common-codes', 'layers', 900, true, 'CODE_MANAGE'), "
            "('메뉴 관리', '/admin/menus', 'list', 910, true, 'MENU_MANAGE')"
        )
    )
