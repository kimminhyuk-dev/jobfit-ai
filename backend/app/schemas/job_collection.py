"""
채용공고 수집 요청/응답 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Work24CollectRequest(BaseModel):
    """Work24 채용정보 수동 수집 요청"""

    keyword: str | None = Field(default=None, max_length=100)
    start_page: int = Field(default=1, ge=1)
    max_pages: int = Field(default=1, ge=1, le=5)
    display: int = Field(default=10, ge=1, le=100)
    region: list[str] | None = None
    occupation: list[str] | None = None
    idempotency_key: str | None = Field(default=None, max_length=100)

    @field_validator("keyword", "idempotency_key")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("region", "occupation")
    @classmethod
    def strip_optional_list(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        stripped = [item.strip() for item in value if item.strip()]
        return stripped or None


class Work24CollectResponse(BaseModel):
    """Work24 채용정보 수동 수집 응답"""

    model_config = ConfigDict(from_attributes=True)

    job_code: str
    status: str
    run_id: int
    collected_count: int
    inserted_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime
    ended_at: datetime | None


class AlioCollectRequest(BaseModel):
    """ALIO 채용정보 수동 수집 요청"""

    keyword: str | None = Field(default=None, max_length=100)
    start_page: int = Field(default=1, ge=1)
    max_pages: int = Field(default=1, ge=1, le=10)
    display: int = Field(default=10, ge=1, le=100)
    idempotency_key: str | None = Field(default=None, max_length=100)

    @field_validator("keyword", "idempotency_key")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class AlioCollectResponse(BaseModel):
    """ALIO 채용정보 수동 수집 응답"""

    model_config = ConfigDict(from_attributes=True)

    job_code: str
    status: str
    collected_count: int
    inserted_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    error_code: str | None = None
    error_message: str | None = None
    run_id: int


class JobPostingResponse(BaseModel):
    """사용자 채용공고 조회 응답"""

    model_config = ConfigDict(from_attributes=True)

    job_id: int
    source: str
    source_job_id: str | None
    source_url: str | None
    company_name: str | None
    title: str
    location: str | None
    location_code: str | None
    career_level: str | None
    career_level_code: str | None
    education: str | None
    education_code: str | None
    employment_type: str | None
    employment_type_code: str | None
    ncs_category: str | None
    ncs_category_code: str | None
    organization_type: str | None
    organization_type_code: str | None
    organization_category: str | None
    organization_category_code: str | None
    ministry: str | None
    ministry_code: str | None
    posted_at: datetime | None
    deadline: datetime | None
    status: str
    collected_at: datetime


class JobPostingListResponse(BaseModel):
    """사용자 채용공고 목록 응답"""

    items: list[JobPostingResponse]
    total: int
    page: int
    size: int
