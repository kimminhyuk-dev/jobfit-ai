"""
인증 관련 요청/응답 스키마
"""

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """로그인 요청"""

    email: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def strip_email_or_business_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("이메일 또는 사업자번호를 입력하세요.")
        return value


class AuthResponse(BaseModel):
    """로그인·회원가입·토큰 갱신 응답 — 토큰은 HttpOnly 쿠키로만 전달한다."""

    user: UserResponse


class MessageResponse(BaseModel):
    """단순 메시지 응답"""

    message: str
