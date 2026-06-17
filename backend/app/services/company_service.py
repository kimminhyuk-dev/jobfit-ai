"""
기업회원 대시보드 비즈니스 로직.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job_posting import JobPosting
from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.company import (
    CompanyApplicantItem,
    CompanyApplicantResumeResponse,
    CompanyDashboardResponse,
    CompanyJobCreateRequest,
    CompanyJobItem,
    CompanyJobUpdateRequest,
)
from app.schemas.resume import (
    ResumeCoverLetterSectionResponse,
    ResumeParsedData,
    ResumeProjectResponse,
)

# 기업이 직접 등록한 공고만 수정/삭제 가능 (외부 수집 공고는 읽기 전용).
EDITABLE_JOB_SOURCE = "MANUAL"
ALLOWED_JOB_STATUSES = {"OPEN", "CLOSED", "HIDDEN"}


class CompanyAccountNotFoundError(Exception):
    """로그인 사용자에 연결된 기업 계정이 없음."""


class CompanyApplicationNotFoundError(Exception):
    """기업에 전달된 해당 지원/이력서를 찾을 수 없음."""


class CompanyJobNotFoundError(Exception):
    """기업에 속한 해당 공고를 찾을 수 없음."""


class CompanyJobNotEditableError(Exception):
    """외부 수집 공고 등 수정할 수 없는 공고."""


class CompanyService:
    """기업회원 관련 비즈니스 로직."""

    def __init__(self, db: Session):
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.application_repository = ApplicationRepository(db)
        self.job_posting_repository = JobPostingRepository(db)
        self.resume_repository = ResumeRepository(db)
        self.user_repository = UserRepository(db)

    def _get_or_create_company_for_user(self, user_id: int) -> Company:
        company = self.company_repository.get_by_user_id(user_id)
        if company is not None:
            return company

        user = self.user_repository.get_by_id(user_id)
        if user is None or (user.role or "").strip().upper() != "COMPANY":
            raise CompanyAccountNotFoundError

        dedup_key = f"user:{user_id}"
        existing = self.company_repository.get_by_dedup_key(dedup_key)
        if existing is not None:
            return existing

        try:
            company = self.company_repository.create(
                user_id=user.user_id,
                company_name=(user.name or user.email or "기업회원")[:200],
                business_number=None,
                dedup_key=dedup_key,
            )
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError as exc:
            self.db.rollback()
            company = self.company_repository.get_by_user_id(user_id)
            if company is None:
                raise CompanyAccountNotFoundError from exc
            return company

    def get_dashboard(self, user_id: int) -> CompanyDashboardResponse:
        company = self._get_or_create_company_for_user(user_id)

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
                viewed_at=row.Application.viewed_at,
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

    def view_applicant_resume(
        self,
        *,
        user_id: int,
        application_id: int,
        request_ip: str | None,
    ) -> CompanyApplicantResumeResponse:
        """지원자 이력서를 열람하고, 첫 열람이면 상태를 VIEWED로 전환한다."""
        company = self._get_or_create_company_for_user(user_id)

        application = self.application_repository.get_active_by_id_for_company(
            application_id, company.company_id
        )
        if application is None:
            raise CompanyApplicationNotFoundError

        resume = self.resume_repository.get_by_id_no_user(application.resume_id)
        if resume is None:
            raise CompanyApplicationNotFoundError

        # 첫 열람이면 VIEWED로 전환하고 커밋한다(지원자가 열람 여부를 확인할 수 있도록).
        self.application_repository.mark_viewed(
            application,
            actor_id=user_id,
            request_ip=request_ip,
        )
        self.db.commit()
        self.db.refresh(application)

        applicant = self.user_repository.get_by_id(application.user_id)
        job = self.job_posting_repository.get_by_id(application.job_id)
        projects = self.resume_repository.get_projects(resume.resume_id)
        sections = self.resume_repository.get_cover_letter_sections(resume.resume_id)

        return CompanyApplicantResumeResponse(
            application_id=application.application_id,
            status=application.status,
            applied_at=application.applied_at,
            viewed_at=application.viewed_at,
            applicant_name=applicant.name if applicant else None,
            applicant_email=applicant.email if applicant else "",
            job_title=job.title if job else "",
            resume_id=resume.resume_id,
            resume_title=resume.title,
            original_filename=resume.original_filename,
            content_type=resume.content_type,
            file_size=resume.file_size,
            parse_status=resume.parse_status,
            parsed_data=(
                ResumeParsedData.model_validate(resume.parsed_data)
                if resume.parsed_data
                else None
            ),
            structured_projects=[
                ResumeProjectResponse.model_validate(p) for p in projects
            ],
            structured_cover_letter_sections=[
                ResumeCoverLetterSectionResponse.model_validate(s) for s in sections
            ],
        )

    def get_applicant_resume_file(self, user_id: int, application_id: int):
        """Return the original resume file for an application owned by this company."""
        company = self._get_or_create_company_for_user(user_id)
        application = self.application_repository.get_active_by_id_for_company(
            application_id, company.company_id
        )
        if application is None:
            raise CompanyApplicationNotFoundError

        resume = self.resume_repository.get_by_id_no_user(application.resume_id)
        if resume is None:
            raise CompanyApplicationNotFoundError
        return resume

    # ------------------------------------------------------------------ #
    # 기업 공고 관리 (확인/등록/수정/삭제)
    # ------------------------------------------------------------------ #

    def list_company_jobs(self, user_id: int) -> list[CompanyJobItem]:
        """기업의 사업자번호/회사명과 일치하는 공고를 최신순으로 조회한다."""
        company = self._get_or_create_company_for_user(user_id)
        postings = self.job_posting_repository.list_by_company(
            company.business_number, company.company_name
        )
        counts = self.application_repository.count_active_by_company_jobs(
            company.company_id
        )
        return [self._to_job_item(p, counts.get(p.job_id, 0)) for p in postings]

    def get_company_job(self, user_id: int, job_id: int) -> CompanyJobItem:
        company = self._get_or_create_company_for_user(user_id)
        posting = self.job_posting_repository.get_company_owned(
            job_id, company.business_number, company.company_name
        )
        if posting is None:
            raise CompanyJobNotFoundError
        counts = self.application_repository.count_active_by_company_jobs(
            company.company_id
        )
        return self._to_job_item(posting, counts.get(posting.job_id, 0))

    def create_company_job(
        self,
        *,
        user_id: int,
        payload: CompanyJobCreateRequest,
        request_ip: str | None,
    ) -> CompanyJobItem:
        company = self._get_or_create_company_for_user(user_id)
        fields = payload.model_dump(exclude={"status"})
        fields["status"] = self._normalize_status(payload.status)
        posting = self.job_posting_repository.create_company_job(
            company_name=company.company_name,
            business_number=company.business_number,
            fields=fields,
            actor_id=user_id,
            request_ip=request_ip,
        )
        self.db.commit()
        self.db.refresh(posting)
        return self._to_job_item(posting, 0)

    def update_company_job(
        self,
        *,
        user_id: int,
        job_id: int,
        payload: CompanyJobUpdateRequest,
        request_ip: str | None,
    ) -> CompanyJobItem:
        company = self._get_or_create_company_for_user(user_id)
        posting = self._get_editable_posting(company, job_id)

        fields = payload.model_dump(exclude_unset=True)
        if "status" in fields and fields["status"] is not None:
            fields["status"] = self._normalize_status(fields["status"])
        self.job_posting_repository.update_fields(
            posting, fields, actor_id=user_id, request_ip=request_ip
        )
        self.db.commit()
        self.db.refresh(posting)
        counts = self.application_repository.count_active_by_company_jobs(
            company.company_id
        )
        return self._to_job_item(posting, counts.get(posting.job_id, 0))

    def delete_company_job(
        self,
        *,
        user_id: int,
        job_id: int,
        request_ip: str | None,
    ) -> None:
        company = self._get_or_create_company_for_user(user_id)
        posting = self._get_editable_posting(company, job_id)
        self.job_posting_repository.soft_delete(
            posting, actor_id=user_id, request_ip=request_ip
        )
        self.db.commit()

    def _get_editable_posting(self, company: Company, job_id: int) -> JobPosting:
        posting = self.job_posting_repository.get_company_owned(
            job_id, company.business_number, company.company_name
        )
        if posting is None:
            raise CompanyJobNotFoundError
        if posting.source != EDITABLE_JOB_SOURCE:
            raise CompanyJobNotEditableError
        return posting

    @staticmethod
    def _normalize_status(status: str | None) -> str:
        normalized = (status or "OPEN").strip().upper()
        return normalized if normalized in ALLOWED_JOB_STATUSES else "OPEN"

    @staticmethod
    def _to_job_item(posting: JobPosting, applicant_count: int) -> CompanyJobItem:
        return CompanyJobItem(
            job_id=posting.job_id,
            title=posting.title,
            company_name=posting.company_name,
            location=posting.location,
            employment_type=posting.employment_type,
            career_level=posting.career_level,
            education=posting.education,
            ncs_category=posting.ncs_category,
            salary_text=posting.salary_text,
            raw_content=posting.raw_content,
            deadline=posting.deadline,
            posted_at=posting.posted_at,
            status=posting.status,
            source=posting.source,
            data_source=posting.data_source,
            editable=posting.source == EDITABLE_JOB_SOURCE,
            applicant_count=applicant_count,
            created_at=posting.created_at,
        )
