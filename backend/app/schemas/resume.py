"""
이력서 요청/응답 스키마
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeProfileData(BaseModel):
    """파싱된 기본 인적사항"""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    birth_date: str | None = None
    email: str | None = None
    phone: str | None = None
    github_url: str | None = None
    urls: list[str] = Field(default_factory=list)
    address: str | None = None


class ResumeParsedData(BaseModel):
    """이력서 파싱 결과 JSON 구조"""

    model_config = ConfigDict(extra="allow")

    profile: ResumeProfileData = Field(default_factory=ResumeProfileData)
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    sections: dict[str, str] = Field(default_factory=dict)
    schools: list[dict[str, Any]] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    training: list[str] = Field(default_factory=list)
    experiences: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    cover_letter: str | None = None
    cover_letter_sections: dict[str, str] = Field(default_factory=dict)
    awards: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    highlights: dict[str, list[str]] = Field(default_factory=dict)
    text_length: int = 0
    parsed_by: str | None = None


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
    parsed_data: ResumeParsedData | None


class ResumeUpdate(BaseModel):
    """이력서 파싱 정보 수정 요청"""

    title: str | None = Field(default=None, max_length=120)
    raw_text: str | None = None
    parsed_data: ResumeParsedData | None = None
