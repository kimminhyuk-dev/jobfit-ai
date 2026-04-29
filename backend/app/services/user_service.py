"""
회원가입, 로그인, 토큰 재발급 비즈니스 로직
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate


class DuplicateEmailError(Exception):
    """이미 가입된 이메일"""


class InvalidCredentialsError(Exception):
    """로그인 정보 불일치"""


class InvalidTokenError(Exception):
    """토큰 검증 실패"""


class InactiveUserError(Exception):
    """비활성 계정"""


class UserService:
    """회원 인증 관련 비즈니스 로직"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def signup(self, user_create: UserCreate, request_ip: str | None) -> User:
        if self.user_repository.get_by_email(str(user_create.email), include_deleted=True):
            raise DuplicateEmailError

        hashed_password = hash_password(user_create.password)

        try:
            user = self.user_repository.create(user_create, hashed_password, request_ip)
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateEmailError from exc

        return user

    def login(self, login_request: LoginRequest) -> User:
        user = self.user_repository.get_by_email(str(login_request.email))
        if user is None or not verify_password(login_request.password, user.password):
            raise InvalidCredentialsError
        if user.status != "ACTIVE":
            raise InactiveUserError
        return user

    def refresh(self, refresh_token: str) -> User:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except (ValueError, TypeError) as exc:
            raise InvalidTokenError from exc

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError
        if user.status != "ACTIVE":
            raise InactiveUserError
        return user

    def create_token_pair(self, user: User) -> tuple[str, str]:
        subject = str(user.user_id)
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        return access_token, refresh_token
