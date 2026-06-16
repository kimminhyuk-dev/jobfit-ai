"""
기업회원 대시보드 응답 스키마
"""

from datetime import datetime

from pydantic import BaseModel


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


class CompanyDashboardResponse(BaseModel):
    """기업회원 대시보드 데이터."""

    company_id: int
    company_name: str | None
    business_number: str | None
    received_count: int
    pending_count: int
    posting_count: int
    applicants: list[CompanyApplicantItem]
