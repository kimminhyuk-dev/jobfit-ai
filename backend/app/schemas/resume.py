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


class ResumeProjectData(BaseModel):
    """파싱된 개별 프로젝트 구조화 데이터"""

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    period: str | None = None
    role: str | None = None
    description: str | None = None
    review: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    raw_text: str | None = None


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
    # projects는 구조화 객체 배열. 구 포맷(str 배열) 호환을 위해 Any 허용.
    projects: list[Any] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    cover_letter: str | None = None
    cover_letter_sections: dict[str, str] = Field(default_factory=dict)
    awards: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    highlights: dict[str, list[str]] = Field(default_factory=dict)
    text_length: int = 0
    parsed_by: str | None = None


# --- 구조화 테이블 응답 스키마 ---

class ResumeProjectResponse(BaseModel):
    """resume_projects 행 응답"""

    model_config = ConfigDict(from_attributes=True)

    project_id: int
    resume_id: int
    order_index: int
    name: str | None
    period: str | None
    role: str | None
    description: str | None
    review: str | None
    tech_stack: list[str] = Field(default_factory=list)
    raw_text: str | None
    created_at: datetime
    updated_at: datetime


class ResumeCoverLetterSectionResponse(BaseModel):
    """resume_cover_letter_sections 행 응답"""

    model_config = ConfigDict(from_attributes=True)

    section_id: int
    resume_id: int
    order_index: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime


# --- 목록·상세 응답 ---

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
    """이력서 상세 응답 (파싱 데이터 + 구조화 테이블 포함)"""

    raw_text: str | None
    parsed_data: ResumeParsedData | None
    structured_projects: list[ResumeProjectResponse] = Field(default_factory=list)
    structured_cover_letter_sections: list[ResumeCoverLetterSectionResponse] = Field(default_factory=list)


class ResumeUpdate(BaseModel):
    """이력서 파싱 정보 수정 요청"""

    title: str | None = Field(default=None, max_length=120)
    raw_text: str | None = None
    parsed_data: ResumeParsedData | None = None
    # 구조화 프로젝트 직접 수정 (선택)
    structured_projects: list[ResumeProjectData] | None = None
    # 구조화 자기소개서 목차 직접 수정 (선택): [{title, content}]
    structured_cover_letter_sections: list[dict[str, str]] | None = None
