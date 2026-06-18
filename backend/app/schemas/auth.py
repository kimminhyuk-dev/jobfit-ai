"""
인증 관련 요청/응답 스키마
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """로그인 요청"""

    email: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)
    portal: Literal["user", "company"] | None = None

    @field_validator("email")
    @classmethod
    def strip_email_or_business_number(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("이메일 또는 사업자번호를 입력하세요.")
        return value


class FindEmailRequest(BaseModel):
    """아이디(이메일) 찾기 요청 - 이름 + 전화번호."""

    name: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=1, max_length=20)


def _normalize_business_number(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 10:
        raise ValueError("사업자등록번호 10자리를 입력하세요.")
    return digits


class CompanyFindEmailRequest(BaseModel):
    """기업 아이디 찾기 요청 - 담당자명 + 사업자등록번호."""

    name: str = Field(min_length=1, max_length=50)
    business_number: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("담당자명을 입력하세요.")
        return value

    @field_validator("business_number")
    @classmethod
    def validate_business_number(cls, value: str) -> str:
        return _normalize_business_number(value)


class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 1단계 - 인증 코드 발송 요청."""

    email: str = Field(min_length=1, max_length=100)


class CompanyPasswordResetRequest(BaseModel):
    """기업 비밀번호 찾기 요청 - 담당자명 + 사업자등록번호 + 이메일."""

    name: str = Field(min_length=1, max_length=50)
    business_number: str = Field(min_length=1, max_length=20)
    email: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("담당자명을 입력하세요.")
        return value

    @field_validator("business_number")
    @classmethod
    def validate_business_number(cls, value: str) -> str:
        return _normalize_business_number(value)

    @field_validator("email")
    @classmethod
    def strip_email(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("이메일을 입력하세요.")
        return value


class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 2단계 - 코드 검증 + 임시 비밀번호 발송."""

    email: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=12)


class FindEmailResponse(BaseModel):
    """아이디 찾기 응답 — 성공 시에만 마스킹된 이메일을 포함한다."""

    message: str
    masked_email: str | None = None


class AuthResponse(BaseModel):
    """로그인·회원가입·토큰 갱신 응답 — 토큰은 HttpOnly 쿠키로만 전달한다."""

    user: UserResponse


class MessageResponse(BaseModel):
    """단순 메시지 응답"""

    message: str
