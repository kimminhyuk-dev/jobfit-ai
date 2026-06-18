"""
기업회원 대시보드 응답 스키마
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from app.models.application import APPLICATION_STATUS_REJECTED

from app.schemas.match_score import ApplicationMatchScoreResponse
from app.schemas.resume import (
    ResumeCoverLetterSectionResponse,
    ResumeParsedData,
    ResumeProjectResponse,
)


class CompanyApplicantItem(BaseModel):
    """기업이 받은 지원 한 건 (지원자/공고/이력서 정보 포함)."""

    application_id: int
    applicant_name: str | None
    applicant_email: str
    job_id: int
    job_title: str
    resume_id: int
    resume_title: str
    status: str
    applied_at: datetime
    viewed_at: datetime | None = None
    match_score: ApplicationMatchScoreResponse | None = None


class CompanyDashboardResponse(BaseModel):
    """기업회원 대시보드 데이터."""

    company_id: int
    company_name: str | None
    business_number: str | None
    address: str | None = None
    received_count: int
    pending_count: int
    posting_count: int
    applicants: list[CompanyApplicantItem]


class CompanyApplicantResumeResponse(BaseModel):
    """기업이 열람하는 지원자 이력서 상세 (열람 시 상태가 VIEWED로 전환됨)."""

    application_id: int
    status: str
    applied_at: datetime
    viewed_at: datetime | None
    applicant_name: str | None
    applicant_email: str
    job_title: str
    resume_id: int
    resume_title: str
    original_filename: str
    content_type: str
    file_size: int
    parse_status: str
    parsed_data: ResumeParsedData | None
    structured_projects: list[ResumeProjectResponse] = Field(default_factory=list)
    structured_cover_letter_sections: list[ResumeCoverLetterSectionResponse] = Field(
        default_factory=list
    )
    match_score: ApplicationMatchScoreResponse | None = None


class CompanyApplicationStatusUpdateRequest(BaseModel):
    """기업이 지원 상태를 수동 변경하는 요청."""

    status: str = Field(min_length=1, max_length=20)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized != APPLICATION_STATUS_REJECTED:
            raise ValueError("이번 단계에서는 탈락(REJECTED) 처리만 변경할 수 있습니다.")
        return normalized


class CompanyApplicationStatusResponse(BaseModel):
    """기업 지원 상태 변경 결과."""

    application_id: int
    status: str
    message: str


class InterviewEmailRequest(BaseModel):
    """면접 안내 메일 발송 요청."""

    interview_at: datetime
    location_address: str | None = Field(
        default=None,
        max_length=500,
        description="면접 장소 주소. 미지정 시 기업 등록 주소(companies.address)를 사용",
    )
    message: str | None = Field(default=None, max_length=2000)

    @field_validator("interview_at")
    @classmethod
    def validate_interview_at(cls, value: datetime) -> datetime:
        """과거 시점의 면접 일정은 허용하지 않는다."""
        if value.tzinfo is None:
            now = datetime.now()
            compare_value = value
        else:
            now = datetime.now(timezone.utc)
            compare_value = value.astimezone(timezone.utc)
        if compare_value <= now:
            raise ValueError("면접 일시는 현재 시각 이후여야 합니다.")
        return value


class InterviewEmailResponse(BaseModel):
    """면접 안내 메일 발송 결과."""

    application_id: int
    to_email: str
    map_attached: bool
    status: str
    message: str


# --- 기업 공고 관리 (확인/등록/수정/삭제) ---

class CompanyJobItem(BaseModel):
    """기업이 관리하는 공고 한 건 (목록/상세 공용)."""

    job_id: int
    title: str
    company_name: str | None
    location: str | None
    employment_type: str | None
    career_level: str | None
    education: str | None
    ncs_category: str | None
    salary_text: str | None
    raw_content: str | None
    deadline: datetime | None
    posted_at: datetime | None
    status: str
    source: str
    data_source: str
    editable: bool
    applicant_count: int
    created_at: datetime


class CompanyJobCreateRequest(BaseModel):
    """기업이 직접 등록하는 공고."""

    title: str = Field(min_length=1, max_length=500)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=50)
    career_level: str | None = Field(default=None, max_length=50)
    education: str | None = Field(default=None, max_length=50)
    ncs_category: str | None = Field(default=None, max_length=200)
    salary_text: str | None = Field(default=None, max_length=500)
    raw_content: str | None = None
    deadline: datetime | None = None
    status: str = Field(default="OPEN")


class CompanyJobUpdateRequest(BaseModel):
    """기업 공고 수정 (전달된 필드만 변경)."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=50)
    career_level: str | None = Field(default=None, max_length=50)
    education: str | None = Field(default=None, max_length=50)
    ncs_category: str | None = Field(default=None, max_length=200)
    salary_text: str | None = Field(default=None, max_length=500)
    raw_content: str | None = None
    deadline: datetime | None = None
    status: str | None = None
