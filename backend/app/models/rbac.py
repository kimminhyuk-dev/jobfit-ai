"""
RBAC(역할 기반 접근 제어) 모델

NIST 표준 RBAC 구조를 따른다.
    users ──< user_roles >── roles ──< role_permissions >── permissions

핵심 원칙:
- 권한(permission)은 사용자에게 직접 부여하지 않고 역할(role)을 통해서만 부여한다.
- 한 사용자는 여러 역할을 가질 수 있고, 한 역할은 여러 권한을 가질 수 있다(다대다).

기존 users.role / users.admin_level 컬럼은 그대로 유지하며, 이 테이블들은
신규 기능(휴가 결재 등)의 권한 판정에 사용한다. 기존 admin_level 동작은 깨지 않는다.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin

# ─────────────────────────────────────────────
# 역할 코드 (시드/백필/호환 셰임에서 공유)
# ─────────────────────────────────────────────
ROLE_SUPER_ADMIN = "SUPER_ADMIN"
ROLE_TEAM_LEAD = "TEAM_LEAD"
ROLE_ADMIN_STAFF = "ADMIN_STAFF"
ROLE_OPS_ADMIN = "OPS_ADMIN"

# ─────────────────────────────────────────────
# 권한 코드 (기능 단위)
# ─────────────────────────────────────────────
PERM_LEAVE_REQUEST = "LEAVE_REQUEST"
PERM_LEAVE_APPROVE = "LEAVE_APPROVE"
PERM_USER_MANAGE = "USER_MANAGE"
PERM_JOB_MANAGE = "JOB_MANAGE"


class Role(Base, AuditMixin):
    """역할 정의 테이블."""

    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="역할 PK",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="역할 코드 (예: SUPER_ADMIN)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="역할 표시명",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="역할 설명",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="활성 여부",
    )

    def __repr__(self) -> str:
        return f"<Role(role_id={self.role_id}, code={self.code})>"


class Permission(Base, AuditMixin):
    """권한(기능 단위) 정의 테이블."""

    __tablename__ = "permissions"

    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="권한 PK",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="권한 코드 (예: LEAVE_APPROVE)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="권한 표시명",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="권한 설명",
    )

    def __repr__(self) -> str:
        return f"<Permission(permission_id={self.permission_id}, code={self.code})>"


class RolePermission(Base):
    """역할-권한 매핑 테이블 (다대다)."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )

    role_permission_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="역할-권한 매핑 PK",
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="역할 role_id",
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("permissions.permission_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="권한 permission_id",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(Base):
    """사용자-역할 매핑 테이블 (다대다)."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    user_role_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="사용자-역할 매핑 PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 user_id",
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="역할 role_id",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
        comment="부여 시각",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="역할을 부여한 user_id (백필/시드는 null)",
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
