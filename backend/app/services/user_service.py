"""
회원가입, 로그인, 토큰 재발급 비즈니스 로직
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserUpdate


class DuplicateEmailError(Exception):
    """이미 가입된 이메일"""


class InvalidCurrentPasswordError(Exception):
    """현재 비밀번호 불일치"""


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
        self.refresh_token_repository = RefreshTokenRepository(db)

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

    def refresh(self, refresh_token: str, ip: str | None = None) -> tuple["User", str, str]:
        """
        Refresh Token을 검증하고 새 토큰 쌍을 발급한다.
        반환값: (user, access_token, new_refresh_token)
        - 이미 취소된 토큰이 다시 들어오면 패밀리 전체를 취소한다 (재사용 공격 대응).
        """
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except (ValueError, TypeError) as exc:
            raise InvalidTokenError from exc

        token_hash = hash_token(refresh_token)
        db_token = self.refresh_token_repository.get_by_hash(token_hash)

        if db_token is None:
            raise InvalidTokenError

        if db_token.is_revoked:
            # 이미 사용된 토큰 재제출 → 패밀리 전체 취소
            self.refresh_token_repository.revoke_family(db_token.family_id)
            self.db.commit()
            raise InvalidTokenError

        if db_token.expires_at <= datetime.now(UTC):
            raise InvalidTokenError

        user = self.user_repository.get_by_id(user_id)
        if user is None or user.status != "ACTIVE":
            raise InactiveUserError

        # 기존 토큰 취소
        self.refresh_token_repository.revoke(db_token)

        # 새 토큰 쌍 발급 (같은 패밀리 유지 → 로테이션 추적 가능)
        access_token = create_access_token(str(user.user_id))
        new_refresh_token = create_refresh_token(str(user.user_id))
        new_hash = hash_token(new_refresh_token)
        new_expires_at = datetime.now(UTC) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
        self.refresh_token_repository.create(
            user_id=user.user_id,
            token_hash=new_hash,
            family_id=db_token.family_id,
            expires_at=new_expires_at,
            created_ip=ip,
        )
        self.db.commit()
        return user, access_token, new_refresh_token

    def logout(self, refresh_token: str) -> None:
        """Refresh Token을 DB에서 취소한다."""
        token_hash = hash_token(refresh_token)
        db_token = self.refresh_token_repository.get_active_by_hash(token_hash)
        if db_token:
            self.refresh_token_repository.revoke(db_token)
            self.db.commit()

    def update_me(
        self,
        user: User,
        user_update: UserUpdate,
        request_ip: str | None = None,
    ) -> User:
        new_hashed: str | None = None
        if user_update.new_password is not None:
            if not user_update.current_password or not verify_password(
                user_update.current_password, user.password
            ):
                raise InvalidCurrentPasswordError
            new_hashed = hash_password(user_update.new_password)

        user = self.user_repository.update(
            user,
            name=user_update.name,
            hashed_password=new_hashed,
            request_ip=request_ip,
        )
        if new_hashed:
            # 비밀번호 변경 시 모든 세션 강제 만료
            self.refresh_token_repository.revoke_all_by_user(user.user_id)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_me(self, user: User, request_ip: str | None = None) -> None:
        """계정을 소프트 삭제하고 모든 세션을 강제 만료한다."""
        self.refresh_token_repository.revoke_all_by_user(user.user_id)
        self.user_repository.soft_delete(user, request_ip=request_ip)
        self.db.commit()

    def create_token_pair(self, user: User, ip: str | None = None) -> tuple[str, str]:
        """Access + Refresh Token 쌍을 발급하고 Refresh Token을 DB에 저장한다."""
        access_token = create_access_token(str(user.user_id))
        refresh_token = create_refresh_token(str(user.user_id))

        token_hash = hash_token(refresh_token)
        family_id = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
        self.refresh_token_repository.create(
            user_id=user.user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
            created_ip=ip,
        )
        self.db.commit()
        return access_token, refresh_token
