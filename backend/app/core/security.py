"""
비밀번호 해시와 JWT 발급/검증 유틸
"""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """평문 비밀번호를 bcrypt 해시로 변환한다."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 저장된 해시가 일치하는지 확인한다."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Access Token을 생성한다."""
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return _create_token(subject=subject, token_type="access", expires_delta=expires_delta)


def create_refresh_token(subject: str) -> str:
    """Refresh Token을 생성한다."""
    expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    return _create_token(subject=subject, token_type="refresh", expires_delta=expires_delta)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """JWT를 검증하고 payload를 반환한다."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("유효하지 않은 토큰입니다.") from exc

    if payload.get("type") != expected_type:
        raise ValueError("토큰 타입이 올바르지 않습니다.")
    if not payload.get("sub"):
        raise ValueError("토큰 subject가 없습니다.")

    return payload


def hash_token(token: str) -> str:
    """토큰을 SHA-256으로 해시한다. DB에는 평문 대신 해시만 저장한다."""
    return hashlib.sha256(token.encode()).hexdigest()


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    expire = now + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
