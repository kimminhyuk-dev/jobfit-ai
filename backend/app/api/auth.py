"""
인증 API 라우터
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.auth import LoginRequest, MessageResponse, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserService,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """UserService 의존성"""
    return UserService(db)


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    user_create: UserCreate,
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """회원가입 후 Access Token을 발급하고 Refresh Token 쿠키를 설정한다."""
    try:
        user = user_service.signup(user_create, request_ip=_get_client_ip(request))
    except DuplicateEmailError:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.DUPLICATE_EMAIL,
            message="이미 가입된 이메일입니다.",
        )

    access_token, refresh_token = user_service.create_token_pair(user)
    _set_refresh_token_cookie(response, refresh_token)
    return _build_token_response(user, access_token)


@router.post("/login", response_model=TokenResponse)
def login(
    login_request: LoginRequest,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """로그인 후 Access Token을 발급하고 Refresh Token 쿠키를 설정한다."""
    try:
        user = user_service.login(login_request)
    except InvalidCredentialsError:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_CREDENTIALS,
            message="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    except InactiveUserError:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.INACTIVE_USER,
            message="활성화되지 않은 계정입니다.",
        )

    access_token, refresh_token = user_service.create_token_pair(user)
    _set_refresh_token_cookie(response, refresh_token)
    return _build_token_response(user, access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """Refresh Token을 검증하고 토큰 쌍을 재발급한다."""
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if not refresh_token:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.REFRESH_TOKEN_MISSING,
            message="Refresh Token이 없습니다.",
        )

    try:
        user = user_service.refresh(refresh_token)
    except InvalidTokenError:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REFRESH_TOKEN,
            message="Refresh Token이 유효하지 않습니다.",
        )
    except InactiveUserError:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.INACTIVE_USER,
            message="활성화되지 않은 계정입니다.",
        )

    new_access_token, new_refresh_token = user_service.create_token_pair(user)
    _set_refresh_token_cookie(response, new_refresh_token)
    return _build_token_response(user, new_access_token)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    """Refresh Token 쿠키를 삭제한다."""
    _clear_refresh_token_cookie(response)
    return MessageResponse(message="로그아웃되었습니다.")


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Access Token으로 현재 로그인 사용자를 조회한다."""
    return UserResponse.model_validate(current_user)


def _build_token_response(user: User, access_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
        path="/auth",
    )


def _clear_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
        path="/auth",
    )


def _get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
