"""
기업회원 대시보드 비즈니스 로직.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.schemas.company import CompanyApplicantItem, CompanyDashboardResponse


class CompanyAccountNotFoundError(Exception):
    """로그인 사용자에 연결된 기업 계정이 없음."""


class CompanyService:
    """기업회원 관련 비즈니스 로직."""

    def __init__(self, db: Session):
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.application_repository = ApplicationRepository(db)
        self.job_posting_repository = JobPostingRepository(db)

    def get_dashboard(self, user_id: int) -> CompanyDashboardResponse:
        company = self.company_repository.get_by_user_id(user_id)
        if company is None:
            raise CompanyAccountNotFoundError

        rows = self.application_repository.list_by_company(company.company_id)
        received_count, pending_count = self.application_repository.count_by_company(
            company.company_id
        )
        posting_count = self.job_posting_repository.count_by_company(
            company.business_number,
            company.company_name,
        )

        applicants = [
            CompanyApplicantItem(
                application_id=row.Application.application_id,
                applicant_name=row.applicant_name,
                applicant_email=row.applicant_email,
                job_id=row.Application.job_id,
                job_title=row.job_title,
                resume_id=row.Application.resume_id,
                resume_title=row.resume_title,
                status=row.Application.status,
                applied_at=row.Application.applied_at,
            )
            for row in rows
        ]

        return CompanyDashboardResponse(
            company_id=company.company_id,
            company_name=company.company_name,
            business_number=company.business_number,
            received_count=received_count,
            pending_count=pending_count,
            posting_count=posting_count,
            applicants=applicants,
        )
