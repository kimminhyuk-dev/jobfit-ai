"""seed rbac roles/permissions and backfill existing admins

- permissions / roles / role_permissions 초기 시드(idempotent).
- 기존 ADMIN 계정을 admin_level 기준으로 user_roles 백필.
    A      -> SUPER_ADMIN
    B/C/NULL -> ADMIN_STAFF

기존 admin_level 동작은 그대로 두고(컬럼/의존성 유지), RBAC는 신규 기능 권한 판정에 사용한다.

Revision ID: r0s1t2u3v4w5
Revises: q9r0s1t2u3v4
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "r0s1t2u3v4w5"
down_revision = "q9r0s1t2u3v4"
branch_labels = None
depends_on = None


# (code, name, description)
PERMISSIONS = [
    ("LEAVE_REQUEST", "휴가 신청", "휴가(연차 등) 신청/조회/취소 권한"),
    ("LEAVE_APPROVE", "휴가 결재", "휴가 신청 승인/반려/일정변경요청 권한"),
    ("USER_MANAGE", "사용자 관리", "사용자 계정·역할 관리 권한"),
    ("JOB_MANAGE", "채용공고 관리", "채용공고 수집·관리 권한"),
]

ROLES = [
    ("SUPER_ADMIN", "최고 관리자", "모든 권한 보유. 팀장 휴가의 최종 결재자"),
    ("TEAM_LEAD", "팀장", "팀원 휴가 1차 결재자"),
    ("ADMIN_STAFF", "관리 담당자", "기본 관리 업무 담당"),
    ("OPS_ADMIN", "운영 관리자", "채용공고 등 운영 업무 담당"),
]

ROLE_PERMISSIONS = {
    "SUPER_ADMIN": ["LEAVE_REQUEST", "LEAVE_APPROVE", "USER_MANAGE", "JOB_MANAGE"],
    "TEAM_LEAD": ["LEAVE_REQUEST", "LEAVE_APPROVE"],
    "ADMIN_STAFF": ["LEAVE_REQUEST", "JOB_MANAGE"],
    "OPS_ADMIN": ["LEAVE_REQUEST", "JOB_MANAGE"],
}


def upgrade() -> None:
    bind = op.get_bind()

    # 1) permissions 시드
    for code, name, description in PERMISSIONS:
        bind.execute(
            sa.text(
                "INSERT INTO permissions (code, name, description) "
                "VALUES (:code, :name, :description) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "name": name, "description": description},
        )

    # 2) roles 시드
    for code, name, description in ROLES:
        bind.execute(
            sa.text(
                "INSERT INTO roles (code, name, description) "
                "VALUES (:code, :name, :description) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {"code": code, "name": name, "description": description},
        )

    # 3) role_permissions 매핑 시드
    for role_code, perm_codes in ROLE_PERMISSIONS.items():
        for perm_code in perm_codes:
            bind.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT r.role_id, p.permission_id "
                    "FROM roles r, permissions p "
                    "WHERE r.code = :role_code AND p.code = :perm_code "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ),
                {"role_code": role_code, "perm_code": perm_code},
            )

    # 4) 기존 ADMIN 백필: A -> SUPER_ADMIN, 그 외 -> ADMIN_STAFF
    bind.execute(
        sa.text(
            "INSERT INTO user_roles (user_id, role_id) "
            "SELECT u.user_id, r.role_id "
            "FROM users u "
            "JOIN roles r ON r.code = CASE WHEN u.admin_level = 'A' "
            "THEN 'SUPER_ADMIN' ELSE 'ADMIN_STAFF' END "
            "WHERE u.role = 'ADMIN' AND u.is_deleted = false "
            "ON CONFLICT (user_id, role_id) DO NOTHING"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    role_codes = [code for code, _, _ in ROLES]
    perm_codes = [code for code, _, _ in PERMISSIONS]

    # 백필/매핑 제거 후 시드 역할·권한 제거 (FK CASCADE에도 명시적으로 정리)
    bind.execute(
        sa.text(
            "DELETE FROM user_roles WHERE role_id IN "
            "(SELECT role_id FROM roles WHERE code = ANY(:codes))"
        ),
        {"codes": role_codes},
    )
    bind.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE role_id IN "
            "(SELECT role_id FROM roles WHERE code = ANY(:codes))"
        ),
        {"codes": role_codes},
    )
    bind.execute(
        sa.text("DELETE FROM roles WHERE code = ANY(:codes)"),
        {"codes": role_codes},
    )
    bind.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)"),
        {"codes": perm_codes},
    )
