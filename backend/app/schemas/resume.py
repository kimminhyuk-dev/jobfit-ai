"""
이력서 요청/응답 스키마
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeParsedData(BaseModel):
    """규칙 기반 파싱 결과"""

    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    text_length: int = 0


class ResumeListItem(BaseModel):
    """이력서 목록 응답"""

    model_config = ConfigDict(from_attributes=True)

    resume_id: int
    user_id: int
    title: str
    original_filename: str
    file_size: int
    content_type: str
    parse_status: str
    parse_error: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ResumeDetail(ResumeListItem):
    """이력서 상세 응답"""

    raw_text: str | None
    parsed_data: dict[str, Any] | None
