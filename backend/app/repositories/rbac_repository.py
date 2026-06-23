"""
RBAC 권한 조회 DB 접근 계층.

권한은 역할을 통해서만 부여된다(NIST 원칙).
    user_roles -> roles -> role_permissions -> permissions
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rbac import Permission, Role, RolePermission, UserRole


class RbacRepository:
    """역할/권한 조회를 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def get_role_codes_for_user(self, user_id: int) -> set[str]:
        """사용자에게 직접 부여된 역할 코드 집합을 조회한다."""
        stmt = (
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.role_id)
            .where(UserRole.user_id == user_id)
            .where(Role.is_active.is_(True))
        )
        return set(self.db.execute(stmt).scalars().all())

    def get_permission_codes_for_user(self, user_id: int) -> set[str]:
        """사용자의 역할들을 경유해 보유한 권한 코드 집합을 조회한다."""
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
            .join(Role, Role.role_id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.role_id)
            .where(UserRole.user_id == user_id)
            .where(Role.is_active.is_(True))
        )
        return set(self.db.execute(stmt).scalars().all())

    def get_permission_codes_for_role_codes(self, role_codes: set[str]) -> set[str]:
        """역할 코드 집합이 보유한 권한 코드 집합을 조회한다(호환 셰임용)."""
        if not role_codes:
            return set()
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
            .join(Role, Role.role_id == RolePermission.role_id)
            .where(Role.code.in_(role_codes))
            .where(Role.is_active.is_(True))
        )
        return set(self.db.execute(stmt).scalars().all())
