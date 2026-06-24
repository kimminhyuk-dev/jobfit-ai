"""공통코드 관리 요청과 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CommonCodeGroupCreate(BaseModel):
    """공통코드 그룹 생성 요청."""

    group_code: str = Field(min_length=1, max_length=30, pattern=r"^[A-Z0-9_:-]+$")
    group_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    sort_order: int = Field(default=0, ge=0)
    use_yn: bool = True
    category_code: str = Field(default="ADM", min_length=1, max_length=30)

    @field_validator("group_code", "group_name", "category_code")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """필수 문자열의 앞뒤 공백을 제거한다."""
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        """설명은 빈 문자열이면 null로 다룬다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class CommonCodeGroupUpdate(BaseModel):
    """공통코드 그룹 수정 요청."""

    group_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    sort_order: int | None = Field(default=None, ge=0)
    use_yn: bool | None = None

    @field_validator("group_name")
    @classmethod
    def strip_group_name(cls, value: str | None) -> str | None:
        """그룹명의 앞뒤 공백을 제거한다."""
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        """설명은 빈 문자열이면 null로 다룬다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class CommonCodeGroupResponse(BaseModel):
    """공통코드 그룹 응답."""

    id: int
    group_code: str
    group_name: str
    description: str | None
    sort_order: int
    use_yn: bool
    category_code: str
    created_at: datetime
    updated_at: datetime
    reg_user_id: int | None = None
    reg_ip: str | None = None
    reg_dt: datetime | None = None
    mod_user_id: int | None = None
    mod_ip: str | None = None
    mod_dt: datetime | None = None


class CommonCodeItemCreate(BaseModel):
    """공통코드 상세 생성 요청."""

    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Z0-9_:-]+$")
    code_name: str = Field(min_length=1, max_length=200)
    sort_order: int = Field(default=0, ge=0)
    use_yn: bool = True
    attr1: str | None = Field(default=None, max_length=255)
    attr2: str | None = Field(default=None, max_length=255)

    @field_validator("code", "code_name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """필수 문자열의 앞뒤 공백을 제거한다."""
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @field_validator("attr1", "attr2")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        """선택 문자열은 빈 문자열이면 null로 다룬다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class CommonCodeItemUpdate(BaseModel):
    """공통코드 상세 수정 요청."""

    code_name: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = Field(default=None, ge=0)
    use_yn: bool | None = None
    attr1: str | None = Field(default=None, max_length=255)
    attr2: str | None = Field(default=None, max_length=255)

    @field_validator("code_name")
    @classmethod
    def strip_code_name(cls, value: str | None) -> str | None:
        """코드명의 앞뒤 공백을 제거한다."""
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @field_validator("attr1", "attr2")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        """선택 문자열은 빈 문자열이면 null로 다룬다."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class CommonCodeItemResponse(BaseModel):
    """공통코드 상세 응답."""

    id: int
    group_code: str
    code: str
    code_name: str
    sort_order: int
    use_yn: bool
    attr1: str | None
    attr2: str | None
    created_at: datetime
    updated_at: datetime
    reg_user_id: int | None = None
    reg_ip: str | None = None
    reg_dt: datetime | None = None
    mod_user_id: int | None = None
    mod_ip: str | None = None
    mod_dt: datetime | None = None
