"""
회원 관련 요청/응답 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """회원가입 요청"""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        """공백만 들어온 이름은 저장하지 않는다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class UserUpdate(BaseModel):
    """회원정보 수정 요청"""

    name: str | None = Field(default=None, max_length=50)
    current_password: str | None = Field(default=None, min_length=1, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class UserResponse(BaseModel):
    """회원 응답"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: EmailStr
    name: str | None
    status: str
    role: str
    created_at: datetime
    updated_at: datetime
