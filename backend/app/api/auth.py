"""
인증 API 라우터
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    CompanyFindEmailRequest,
    CompanyPasswordResetRequest,
    FindEmailResponse,
    FindEmailRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.account_recovery_service import (
    AccountRecoveryService,
    PasswordResetEmailError,
    RecoveryRateLimitedError,
)
from app.services.user_service import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidTokenError,
    UserService,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_account_recovery_service(
    db: Session = Depends(get_db),
) -> AccountRecoveryService:
    return AccountRecoveryService(db)


def _normalized_role(user: User) -> str:
    return (user.role or "").strip().upper()


def _raise_recovery_rate_limit() -> None:
    raise AppException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        code=ErrorCode.EMAIL_RATE_LIMITED,
        message="잠시 후 다시 시도해 주세요.",
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    user_create: UserCreate,
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> AuthResponse:
    """회원가입 후 Access·Refresh Token을 HttpOnly 쿠키로 설정한다."""
    try:
        user = user_service.signup(user_create, request_ip=get_client_ip(request))
    except DuplicateEmailError:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.DUPLICATE_EMAIL,
            message="이미 가입된 이메일입니다.",
        )

    ip = get_client_ip(request)
    access_token, refresh_token = user_service.create_token_pair(user, ip=ip)
    _set_token_cookies(response, access_token, refresh_token)
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(
    login_request: LoginRequest,
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> AuthResponse:
    """로그인 후 Access·Refresh Token을 HttpOnly 쿠키로 설정한다."""
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

    role = _normalized_role(user)
    if (login_request.portal == "user" and role != "USER") or (
        login_request.portal == "company"
        and role not in {"COMPANY", "ADMIN"}
    ):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_CREDENTIALS,
            message="로그인 유형에 맞는 계정을 사용해 주세요.",
        )

    ip = get_client_ip(request)
    access_token, refresh_token = user_service.create_token_pair(user, ip=ip)
    _set_token_cookies(response, access_token, refresh_token)
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> AuthResponse:
    """Refresh Token 쿠키를 검증하고 토큰 쌍을 재발급한다."""
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if not refresh_token:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.REFRESH_TOKEN_MISSING,
            message="Refresh Token이 없습니다.",
        )

    try:
        ip = get_client_ip(request)
        user, access_token, new_refresh_token = user_service.refresh(refresh_token, ip=ip)
    except InvalidTokenError:
        _clear_token_cookies(response)
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.INVALID_REFRESH_TOKEN,
            message="Refresh Token이 유효하지 않습니다.",
        )
    except InactiveUserError:
        _clear_token_cookies(response)
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.INACTIVE_USER,
            message="활성화되지 않은 계정입니다.",
        )

    _set_token_cookies(response, access_token, new_refresh_token)
    return AuthResponse(user=UserResponse.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> MessageResponse:
    """Refresh Token을 DB에서 취소하고 쿠키를 삭제한다."""
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if refresh_token:
        user_service.logout(refresh_token)
    _clear_token_cookies(response)
    return MessageResponse(message="로그아웃되었습니다.")


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Access Token 쿠키로 현재 로그인 사용자를 조회한다."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """현재 로그인 사용자의 이름 또는 비밀번호를 수정한다."""
    try:
        user = user_service.update_me(
            current_user,
            user_update,
            request_ip=get_client_ip(request),
        )
    except InvalidCurrentPasswordError:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.INVALID_CREDENTIALS,
            message="현재 비밀번호가 올바르지 않습니다.",
        )
    return UserResponse.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> Response:
    """현재 로그인 사용자의 계정을 소프트 삭제하고 모든 세션을 강제 만료한다."""
    user_service.delete_me(current_user, request_ip=get_client_ip(request))
    _clear_token_cookies(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── 계정 복구 (비로그인): 아이디 찾기 / 비밀번호 재설정 ───────────────────────

@router.post("/find-email", response_model=FindEmailResponse)
def find_email(
    payload: FindEmailRequest,
    recovery_service: AccountRecoveryService = Depends(get_account_recovery_service),
) -> FindEmailResponse:
    """이름+전화로 가입 아이디를 찾아 본인 이메일로 발송한다.

    개인 아이디 찾기는 성공 시 화면에 마스킹 이메일을 표시하고 메일도 발송한다.
    """
    try:
        masked_email = recovery_service.find_email(
            name=payload.name,
            phone=payload.phone,
        )
    except RecoveryRateLimitedError:
        _raise_recovery_rate_limit()
    if masked_email:
        return FindEmailResponse(
            message="가입 이메일로 아이디 안내 메일을 보내드렸습니다.",
            masked_email=masked_email,
        )
    return FindEmailResponse(
        message="일치하는 정보를 찾을 수 없습니다. 입력한 정보를 다시 확인해 주세요."
    )


@router.post("/company/find-email", response_model=FindEmailResponse)
def find_company_email(
    payload: CompanyFindEmailRequest,
    recovery_service: AccountRecoveryService = Depends(get_account_recovery_service),
) -> FindEmailResponse:
    """담당자명+사업자등록번호로 기업 아이디를 찾아 본인 이메일로 발송한다."""
    try:
        masked_email = recovery_service.find_company_email(
            name=payload.name,
            business_number=payload.business_number,
        )
    except RecoveryRateLimitedError:
        _raise_recovery_rate_limit()
    if masked_email:
        return FindEmailResponse(
            message="가입 이메일로 아이디 안내 메일을 보내드렸습니다.",
            masked_email=masked_email,
        )
    return FindEmailResponse(
        message="일치하는 정보를 찾을 수 없습니다. 입력한 정보를 다시 확인해 주세요."
    )


@router.post("/password/reset-request", response_model=MessageResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    recovery_service: AccountRecoveryService = Depends(get_account_recovery_service),
) -> MessageResponse:
    """비밀번호 재설정 인증 코드를 이메일로 발송한다(계정 존재 비노출)."""
    try:
        recovery_service.request_password_reset(email=payload.email)
    except RecoveryRateLimitedError:
        _raise_recovery_rate_limit()
    return MessageResponse(
        message="가입된 이메일이면 인증 코드를 보내드렸습니다. 메일을 확인해 주세요."
    )


@router.post("/company/password/reset-request", response_model=MessageResponse)
def request_company_password_reset(
    payload: CompanyPasswordResetRequest,
    recovery_service: AccountRecoveryService = Depends(get_account_recovery_service),
) -> MessageResponse:
    """기업 비밀번호 찾기: 담당자명+사업자번호+이메일 일치 시 인증 코드를 발송한다."""
    try:
        recovery_service.request_company_password_reset(
            name=payload.name,
            business_number=payload.business_number,
            email=payload.email,
        )
    except RecoveryRateLimitedError:
        _raise_recovery_rate_limit()
    return MessageResponse(
        message="가입된 이메일이면 인증 코드를 보내드렸습니다. 메일을 확인해 주세요."
    )


@router.post("/password/reset-confirm", response_model=MessageResponse)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    recovery_service: AccountRecoveryService = Depends(get_account_recovery_service),
) -> MessageResponse:
    """인증 코드를 검증하고 임시 비밀번호를 이메일로 발송한다."""
    try:
        success = recovery_service.confirm_password_reset(
            email=payload.email, code=payload.code
        )
    except RecoveryRateLimitedError:
        _raise_recovery_rate_limit()
    except PasswordResetEmailError as exc:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.EMAIL_SEND_FAILED,
            message="임시 비밀번호 메일 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc

    if not success:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.PASSWORD_RESET_INVALID_CODE,
            message="인증 코드가 올바르지 않거나 만료되었습니다.",
        )
    return MessageResponse(
        message="임시 비밀번호를 이메일로 보내드렸습니다. 로그인 후 비밀번호를 변경해 주세요."
    )


# ── 쿠키 헬퍼 ──────────────────────────────────────────────────────────────

def _set_token_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    access_max_age = settings.jwt_access_token_expire_minutes * 60
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=settings.access_token_cookie_secure,
        samesite=settings.access_token_cookie_samesite,
        path="/",
    )
    refresh_max_age = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
        path="/auth",
    )


def _clear_token_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.access_token_cookie_name,
        httponly=True,
        secure=settings.access_token_cookie_secure,
        samesite=settings.access_token_cookie_samesite,
        path="/",
    )
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
        path="/auth",
    )
