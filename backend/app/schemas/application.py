"""
지원(이력서 보내기) 요청/응답 스키마
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.match_score import ApplicationMatchScoreResponse


class ApplicationCreateRequest(BaseModel):
    """공고에 이력서를 보내는 지원 요청."""

    job_id: int
    resume_id: int


class ApplicationResponse(BaseModel):
    """지원 생성 결과."""

    model_config = ConfigDict(from_attributes=True)

    application_id: int
    job_id: int
    resume_id: int
    company_id: int | None
    status: str
    applied_at: datetime
    match_score: ApplicationMatchScoreResponse | None = None


class MyApplicationItem(BaseModel):
    """내 지원현황 한 건 (공고/이력서 정보 포함)."""

    application_id: int
    job_id: int
    job_title: str
    company_name: str | None
    source_url: str | None
    resume_id: int
    resume_title: str
    status: str
    applied_at: datetime
    viewed_at: datetime | None = None
    match_score: ApplicationMatchScoreResponse | None = None
