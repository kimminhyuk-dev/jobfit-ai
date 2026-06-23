"""rebackfill B admins with team lead role

Revision ID: s1t2u3v4w5x6
Revises: r0s1t2u3v4w5
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "s1t2u3v4w5x6"
down_revision = "r0s1t2u3v4w5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # B등급 관리자는 휴가 결재자(TEAM_LEAD)이면서 기존 관리자 업무
    # 성격(ADMIN_STAFF)도 유지한다.
    bind.execute(
        sa.text(
            """
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.user_id, r.role_id
            FROM users u
            JOIN roles r ON r.code = 'TEAM_LEAD'
            WHERE u.role = 'ADMIN'
              AND u.admin_level = 'B'
              AND u.is_deleted = false
            ON CONFLICT (user_id, role_id) DO NOTHING
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.user_id, r.role_id
            FROM users u
            JOIN roles r ON r.code = 'ADMIN_STAFF'
            WHERE u.role = 'ADMIN'
              AND (u.admin_level IN ('B', 'C') OR u.admin_level IS NULL)
              AND u.is_deleted = false
            ON CONFLICT (user_id, role_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            DELETE FROM user_roles ur
            USING users u, roles r
            WHERE ur.user_id = u.user_id
              AND ur.role_id = r.role_id
              AND u.role = 'ADMIN'
              AND u.admin_level = 'B'
              AND r.code = 'TEAM_LEAD'
            """
        )
    )
