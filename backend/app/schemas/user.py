"""
회원 관련 요청/응답 스키마

프로필 입력값은 현업 수준의 정규화/필터링을 적용한다.
- 전화번호: 숫자만 추출 후 휴대폰 형식 검증, 하이픈 형식으로 정규화 저장
- 우편번호: 5자리 숫자
- 생년월일: 미래/비현실적 연도 차단
- 주소: 제어문자 제거, 꺾쇠(<>) 차단, 길이 제한
- 기술스택: 항목별 허용문자/길이 제한, 중복 제거, 최대 개수 제한
"""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# 정규화/필터링 상수
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_PHONE_DIGITS = re.compile(r"^01[016789]\d{7,8}$")
_TECH_ALLOWED = re.compile(r"^[\w가-힣+#./\- ]+$")
MAX_TECH_ITEM_LEN = 30
MAX_TECH_COUNT = 50

Gender = Literal["MALE", "FEMALE"]


def _clean_text(value: str | None) -> str | None:
    """제어문자 제거 + 공백 정리. 빈 값은 None."""
    if value is None:
        return None
    cleaned = _CONTROL_CHARS.sub("", str(value)).strip()
    return cleaned or None


class ProfileBase(BaseModel):
    """프로필 입력 필드와 공통 검증 로직."""

    birth_date: date | None = None
    phone: str | None = Field(default=None, max_length=20)
    gender: Gender | None = None
    zipcode: str | None = Field(default=None, max_length=10)
    address1: str | None = Field(default=None, max_length=255)
    address2: str | None = Field(default=None, max_length=255)
    tech_stack: list[str] | None = Field(default=None)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        if not digits:
            return None
        if not _PHONE_DIGITS.fullmatch(digits):
            raise ValueError("올바른 휴대폰 번호를 입력하세요.")
        if len(digits) == 11:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

    @field_validator("zipcode")
    @classmethod
    def normalize_zipcode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        if not digits:
            return None
        if not re.fullmatch(r"\d{5}", digits):
            raise ValueError("우편번호는 5자리 숫자여야 합니다.")
        return digits

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date | None) -> date | None:
        if value is None:
            return None
        if value > date.today():
            raise ValueError("생년월일은 미래일 수 없습니다.")
        if value.year < 1900:
            raise ValueError("생년월일을 확인하세요.")
        return value

    @field_validator("address1", "address2")
    @classmethod
    def clean_address(cls, value: str | None) -> str | None:
        cleaned = _clean_text(value)
        if cleaned is None:
            return None
        if "<" in cleaned or ">" in cleaned:
            raise ValueError("주소에 사용할 수 없는 문자가 포함되어 있습니다.")
        return cleaned

    @field_validator("tech_stack")
    @classmethod
    def normalize_tech_stack(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            token = _CONTROL_CHARS.sub("", str(item)).strip()
            if not token:
                continue
            if len(token) > MAX_TECH_ITEM_LEN:
                raise ValueError(f"기술스택 항목은 {MAX_TECH_ITEM_LEN}자 이하여야 합니다.")
            if not _TECH_ALLOWED.fullmatch(token):
                raise ValueError("기술스택에 사용할 수 없는 문자가 포함되어 있습니다.")
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(token)
            if len(result) > MAX_TECH_COUNT:
                raise ValueError(f"기술스택은 최대 {MAX_TECH_COUNT}개까지 등록할 수 있습니다.")
        return result


class UserCreate(ProfileBase):
    """회원가입 요청"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return _clean_text(value)


class UserUpdate(ProfileBase):
    """회원정보 수정 요청 (부분 수정)."""

    name: str | None = Field(default=None, max_length=50)
    current_password: str | None = Field(default=None, min_length=1, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return _clean_text(value)


class UserResponse(BaseModel):
    """회원 응답"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    # 응답 모델은 이메일을 재검증하지 않는다. 데모/기업 계정은 내부용 .local 도메인을
    # 쓰는데 EmailStr이 .local 같은 예약 도메인을 거부하므로 str로 둔다.
    email: str
    name: str | None
    status: str
    role: str
    admin_level: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    gender: str | None = None
    zipcode: str | None = None
    address1: str | None = None
    address2: str | None = None
    tech_stack: list[str] | None = None
    created_at: datetime
    updated_at: datetime
