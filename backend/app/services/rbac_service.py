"""사용자 역할 부여/회수 비즈니스 로직.

기존 RBAC(user_roles/roles/permissions) 위에서 동작하며, 부여/회수는
ORM 이벤트를 통해 audit_logs 에 자동 기록된다.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.rbac import ROLE_SUPER_ADMIN
from app.repositories.rbac_repository import RbacRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_role import (
    AssignableRole,
    RolePermissionItem,
    UserRolesResponse,
)


class RbacServiceError(Exception):
    """역할 관리 도메인 오류의 기반 예외."""


class TargetUserNotFoundError(RbacServiceError):
    """대상 사용자를 찾을 수 없다."""


class RoleNotFoundError(RbacServiceError):
    """역할 코드를 찾을 수 없다."""


class RoleAlreadyAssignedError(RbacServiceError):
    """이미 보유한 역할을 다시 부여하려 한다."""


class RoleNotAssignedError(RbacServiceError):
    """보유하지 않은 역할을 회수하려 한다."""


class SelfSuperAdminRevokeError(RbacServiceError):
    """자기 자신의 최고관리자 역할을 회수하려 한다."""


class LastSuperAdminError(RbacServiceError):
    """시스템의 마지막 최고관리자를 회수하려 한다."""


class RbacService:
    """사용자 역할 조회/부여/회수를 담당한다."""

    def __init__(self, db: Session):
        self.db = db
        self.rbac_repo = RbacRepository(db)
        self.user_repo = UserRepository(db)

    def get_user_roles(self, user_id: int) -> UserRolesResponse:
        """사용자의 보유 역할과 부여 가능한 전체 역할(권한 포함)을 조회한다."""
        user = self._require_user(user_id)

        assigned = sorted(self.rbac_repo.get_role_codes_for_user(user_id))
        available_roles = self._build_available_roles()
        super_admin_count = self.rbac_repo.count_users_with_role_code(ROLE_SUPER_ADMIN)

        return UserRolesResponse(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            assigned_role_codes=assigned,
            super_admin_count=super_admin_count,
            available_roles=available_roles,
        )

    def assign_role(
        self,
        user_id: int,
        role_code: str,
        *,
        actor_id: int | None,
    ) -> UserRolesResponse:
        """사용자에게 역할을 부여한다. 이미 보유한 경우 차단한다."""
        self._require_user(user_id)
        role = self._require_role(role_code)

        if self.rbac_repo.get_user_role(user_id, role.role_id) is not None:
            raise RoleAlreadyAssignedError(role_code)

        self.rbac_repo.assign_role(user_id, role.role_id, actor_id)
        self.db.commit()
        return self.get_user_roles(user_id)

    def revoke_role(
        self,
        user_id: int,
        role_code: str,
        *,
        actor_id: int,
    ) -> UserRolesResponse:
        """사용자의 역할을 회수한다. 최고관리자 안전장치를 강제한다."""
        self._require_user(user_id)
        role = self._require_role(role_code)

        user_role = self.rbac_repo.get_user_role(user_id, role.role_id)
        if user_role is None:
            raise RoleNotAssignedError(role_code)

        if role.code == ROLE_SUPER_ADMIN:
            if user_id == actor_id:
                raise SelfSuperAdminRevokeError(role_code)
            if self.rbac_repo.count_users_with_role_code(ROLE_SUPER_ADMIN) <= 1:
                raise LastSuperAdminError(role_code)

        self.rbac_repo.revoke_role(user_role)
        self.db.commit()
        return self.get_user_roles(user_id)

    def _require_user(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise TargetUserNotFoundError(str(user_id))
        return user

    def _require_role(self, role_code: str):
        role = self.rbac_repo.get_role_by_code(role_code)
        if role is None:
            raise RoleNotFoundError(role_code)
        return role

    def _build_available_roles(self) -> list[AssignableRole]:
        roles = self.rbac_repo.list_active_roles()
        permissions_by_role = self.rbac_repo.get_permissions_by_role()
        result: list[AssignableRole] = []
        for role in roles:
            permissions = [
                RolePermissionItem(code=perm.code, name=perm.name)
                for perm in permissions_by_role.get(role.role_id, [])
            ]
            result.append(
                AssignableRole(
                    code=role.code,
                    name=role.name,
                    description=role.description,
                    permissions=permissions,
                )
            )
        return result
