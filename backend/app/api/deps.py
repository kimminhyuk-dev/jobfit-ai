"""
FastAPI 의존성 모음
"""

from collections.abc import Callable

from fastapi import Depends, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.security import decode_token
from app.models.rbac import ROLE_ADMIN_STAFF, ROLE_SUPER_ADMIN, ROLE_TEAM_LEAD
from app.models.user import User
from app.repositories.rbac_repository import RbacRepository
from app.repositories.user_repository import UserRepository


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Access Token 쿠키로 현재 로그인 사용자를 조회한다."""
    token = request.cookies.get(settings.access_token_cookie_name)
    if not token:
        raise _unauthorized()

    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise _unauthorized()

    user = UserRepository(db).get_by_id(user_id)
    if user is None or user.status != "ACTIVE":
        raise _unauthorized()
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """현재 사용자가 관리자 권한인지 확인한다."""
    if current_user.role != "ADMIN":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="관리자 권한이 필요합니다.",
        )
    return current_user


def get_current_a_admin_user(
    current_user: User = Depends(get_current_admin_user),
) -> User:
    """현재 사용자가 A등급 관리자 권한인지 확인한다."""
    if current_user.admin_level != "A":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="A등급 관리자 권한이 필요합니다.",
        )
    return current_user


def _legacy_role_codes(user: User) -> set[str]:
    """기존 role/admin_level 기반의 호환 역할 코드를 유도한다.

    백필 마이그레이션과 동일한 매핑을 사용해, user_roles가 아직 없는
    기존 ADMIN 계정도 권한 판정에서 누락되지 않게 한다.
    """
    if user.role == "ADMIN":
        if user.admin_level == "A":
            return {ROLE_SUPER_ADMIN}
        if user.admin_level == "B":
            return {ROLE_TEAM_LEAD, ROLE_ADMIN_STAFF}
        return {ROLE_ADMIN_STAFF}
    return set()


def get_user_permission_codes(db: Session, user: User) -> set[str]:
    """사용자가 보유한 권한 코드 집합을 반환한다(명시 역할 + 호환 셰임 합집합)."""
    repo = RbacRepository(db)
    codes = repo.get_permission_codes_for_user(user.user_id)
    legacy_roles = _legacy_role_codes(user)
    if legacy_roles:
        codes |= repo.get_permission_codes_for_role_codes(legacy_roles)
    return codes


def require_permission(permission_code: str) -> Callable[..., User]:
    """지정한 권한을 보유한 사용자만 통과시키는 의존성을 생성한다.

    권한은 역할을 통해서만 부여된다(NIST 원칙 — 사용자 직접 부여 금지).
    기존 ADMIN 계정은 호환 셰임으로 폴백되어 백필 전에도 동작한다.
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if permission_code not in get_user_permission_codes(db, current_user):
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ErrorCode.FORBIDDEN,
                message="해당 작업을 수행할 권한이 없습니다.",
            )
        return current_user

    return dependency


def get_client_ip(request: Request) -> str | None:
    """프록시 환경을 고려해 요청 클라이언트 IP를 얻는다."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _unauthorized() -> AppException:
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.UNAUTHORIZED,
        message="인증 정보가 유효하지 않습니다.",
    )
