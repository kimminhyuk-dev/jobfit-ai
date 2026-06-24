"""
RBAC 권한 조회 DB 접근 계층.

권한은 역할을 통해서만 부여된다(NIST 원칙).
    user_roles -> roles -> role_permissions -> permissions
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.rbac import Permission, Role, RolePermission, UserRole


class RbacRepository:
    """역할/권한 조회와 부여/회수를 담당한다."""

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

    def list_active_roles(self) -> list[Role]:
        """부여 가능한 활성 역할 목록을 코드 순으로 조회한다."""
        stmt = select(Role).where(Role.is_active.is_(True)).order_by(Role.role_id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_role_by_code(self, role_code: str) -> Role | None:
        """역할 코드로 활성 역할을 조회한다."""
        stmt = (
            select(Role)
            .where(Role.code == role_code)
            .where(Role.is_active.is_(True))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_permissions_by_role(self) -> dict[int, list[Permission]]:
        """활성 역할별 권한 목록을 role_id 기준으로 묶어 조회한다."""
        stmt = (
            select(Role.role_id, Permission)
            .join(RolePermission, RolePermission.role_id == Role.role_id)
            .join(Permission, Permission.permission_id == RolePermission.permission_id)
            .where(Role.is_active.is_(True))
            .order_by(Role.role_id.asc(), Permission.permission_id.asc())
        )
        grouped: dict[int, list[Permission]] = {}
        for role_id, permission in self.db.execute(stmt).all():
            grouped.setdefault(role_id, []).append(permission)
        return grouped

    def get_user_role(self, user_id: int, role_id: int) -> UserRole | None:
        """특정 사용자-역할 매핑을 조회한다."""
        stmt = (
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .where(UserRole.role_id == role_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def count_users_with_role_code(self, role_code: str) -> int:
        """해당 역할 코드를 보유한 사용자 수를 센다(마지막 최고관리자 가드용)."""
        stmt = (
            select(func.count(func.distinct(UserRole.user_id)))
            .join(Role, Role.role_id == UserRole.role_id)
            .where(Role.code == role_code)
        )
        return int(self.db.execute(stmt).scalar_one())

    def assign_role(self, user_id: int, role_id: int, actor_id: int | None) -> UserRole:
        """사용자에게 역할을 부여한다(감사 로그는 ORM 이벤트가 자동 기록)."""
        user_role = UserRole(user_id=user_id, role_id=role_id, created_by=actor_id)
        self.db.add(user_role)
        self.db.flush()
        return user_role

    def revoke_role(self, user_role: UserRole) -> None:
        """사용자 역할 매핑을 회수한다(감사 로그는 ORM 이벤트가 자동 기록)."""
        self.db.delete(user_role)
        self.db.flush()
