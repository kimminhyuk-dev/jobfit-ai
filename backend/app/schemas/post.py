"""
게시글 관련 요청/응답 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    """게시글 생성 요청"""

    category_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("title", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value


class PostUpdate(BaseModel):
    """게시글 수정 요청"""

    category_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1, max_length=5000)

    @field_validator("title", "content")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value


class PostResponse(BaseModel):
    """게시글 응답"""

    model_config = ConfigDict(from_attributes=True)

    post_id: int
    author_id: int
    category_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
