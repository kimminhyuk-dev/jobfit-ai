"""
인증 관련 요청/응답 스키마
"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """로그인 요청"""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    """로그인·회원가입·토큰 갱신 응답 — 토큰은 HttpOnly 쿠키로만 전달한다."""

    user: UserResponse


class MessageResponse(BaseModel):
    """단순 메시지 응답"""

    message: str
