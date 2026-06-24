"""관리자 메뉴 관리 요청과 응답 스키마."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MenuCreate(BaseModel):
    """메뉴 생성 요청."""

    parent_id: int | None = Field(default=None, ge=1)
    menu_name: str = Field(min_length=1, max_length=100)
    menu_url: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=50)
    sort_order: int = Field(default=0, ge=0)
    use_yn: bool = True
    required_permission: str | None = Field(default=None, max_length=50)

    @field_validator("menu_name")
    @classmethod
    def strip_menu_name(cls, value: str) -> str:
        """메뉴명의 앞뒤 공백을 제거한다."""
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @field_validator("menu_url", "icon", "required_permission")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        """선택 문자열은 빈 문자열이면 null로 다룬다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class MenuUpdate(BaseModel):
    """메뉴 수정 요청."""

    parent_id: int | None = Field(default=None, ge=1)
    menu_name: str | None = Field(default=None, min_length=1, max_length=100)
    menu_url: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=50)
    sort_order: int | None = Field(default=None, ge=0)
    use_yn: bool | None = None
    required_permission: str | None = Field(default=None, max_length=50)

    @field_validator("menu_name")
    @classmethod
    def strip_menu_name(cls, value: str | None) -> str | None:
        """메뉴명의 앞뒤 공백을 제거한다."""
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @field_validator("menu_url", "icon", "required_permission")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        """선택 문자열은 빈 문자열이면 null로 다룬다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class MenuResponse(BaseModel):
    """메뉴 응답."""

    id: int
    parent_id: int | None
    menu_name: str
    menu_url: str | None
    icon: str | None
    sort_order: int
    use_yn: bool
    required_permission: str | None
    created_at: datetime
    updated_at: datetime
    reg_user_id: int | None = None
    reg_ip: str | None = None
    reg_dt: datetime | None = None
    mod_user_id: int | None = None
    mod_ip: str | None = None
    mod_dt: datetime | None = None


class MenuTreeResponse(MenuResponse):
    """메뉴 트리 응답."""

    children: list[MenuTreeResponse] = Field(default_factory=list)
