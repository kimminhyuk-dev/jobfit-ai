"""
FastAPI 의존성 모음
"""

from fastapi import Depends, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.security import decode_token
from app.models.user import User
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


def _unauthorized() -> AppException:
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.UNAUTHORIZED,
        message="인증 정보가 유효하지 않습니다.",
    )
