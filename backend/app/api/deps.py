"""
FastAPI 의존성 모음
"""

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Access Token으로 현재 로그인 사용자를 조회한다."""
    if credentials is None:
        raise _invalid_credentials_exception()

    try:
        token = credentials.credentials
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise _invalid_credentials_exception()

    user = UserRepository(db).get_by_id(user_id)
    if user is None or user.status != "ACTIVE":
        raise _invalid_credentials_exception()
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


def _invalid_credentials_exception() -> AppException:
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.UNAUTHORIZED,
        message="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
