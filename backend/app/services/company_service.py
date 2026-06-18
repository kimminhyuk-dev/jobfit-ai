"""
기업회원 대시보드 비즈니스 로직.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.application import (
    APPLICATION_STATUS_INTERVIEW,
    COMPANY_MANUAL_APPLICATION_STATUSES,
)
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.schemas.company import (
    CompanyApplicationStatusResponse,
    CompanyApplicantItem,
    CompanyApplicantResumeResponse,
    CompanyDashboardResponse,
    CompanyJobCreateRequest,
    CompanyJobItem,
    CompanyJobUpdateRequest,
    InterviewEmailRequest,
    InterviewEmailResponse,
)
from app.schemas.match_score import ApplicationMatchScoreResponse
from app.schemas.resume import (
    ResumeCoverLetterSectionResponse,
    ResumeParsedData,
    ResumeProjectResponse,
)
from app.services.email_service import EmailConfigError, EmailSendError
from app.services.interview_email_service import InterviewEmailService
from app.services.match_score_service import MatchScoreService

# 기업이 직접 등록한 공고만 수정/삭제 가능 (외부 수집 공고는 읽기 전용).
EDITABLE_JOB_SOURCE = "MANUAL"
ALLOWED_JOB_STATUSES = {"OPEN", "CLOSED", "HIDDEN"}


class CompanyAccountNotFoundError(Exception):
    """로그인 사용자에 연결된 기업 계정이 없음."""


class CompanyApplicationNotFoundError(Exception):
    """기업에 전달된 해당 지원/이력서를 찾을 수 없음."""


class CompanyApplicationInvalidStatusError(Exception):
    """기업이 직접 변경할 수 없는 지원 상태."""


class CompanyJobNotFoundError(Exception):
    """기업에 속한 해당 공고를 찾을 수 없음."""


class CompanyJobNotEditableError(Exception):
    """외부 수집 공고 등 수정할 수 없는 공고."""


class InterviewLocationMissingError(Exception):
    """면접 장소 주소가 없음(기업 주소 미등록 + 요청에도 주소 없음)."""


class InterviewEmailSendError(Exception):
    """면접 안내 메일 발송 실패."""


class CompanyService:
    """기업회원 관련 비즈니스 로직."""

    def __init__(self, db: Session):
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.application_repository = ApplicationRepository(db)
        self.job_posting_repository = JobPostingRepository(db)
        self.resume_repository = ResumeRepository(db)
        self.user_repository = UserRepository(db)
        self.match_score_service = MatchScoreService(db)

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
        match_scores = self._ensure_match_scores_for_rows(rows, actor_id=user_id)

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
                match_score=match_scores.get(row.Application.application_id),
            )
            for row in rows
        ]

        return CompanyDashboardResponse(
            company_id=company.company_id,
            company_name=company.company_name,
            business_number=company.business_number,
            address=company.address,
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

        applicant = self.user_repository.get_by_id(application.user_id)
        job = self.job_posting_repository.get_by_id(application.job_id)
        if job is None:
            raise CompanyApplicationNotFoundError
        match_score = self.match_score_service.ensure_score_for_application(
            application,
            resume,
            job,
            actor_id=user_id,
            request_ip=request_ip,
        )
        match_score_response = ApplicationMatchScoreResponse.model_validate(match_score)
        self.db.commit()
        self.db.refresh(application)
        projects = self.resume_repository.get_projects(resume.resume_id)
        sections = self.resume_repository.get_cover_letter_sections(resume.resume_id)

        return CompanyApplicantResumeResponse(
            application_id=application.application_id,
            status=application.status,
            applied_at=application.applied_at,
            viewed_at=application.viewed_at,
            applicant_name=applicant.name if applicant else None,
            applicant_email=applicant.email if applicant else "",
            job_title=job.title,
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
            match_score=match_score_response,
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

    def send_interview_email(
        self,
        *,
        user_id: int,
        application_id: int,
        payload: InterviewEmailRequest,
        request_ip: str | None,
    ) -> InterviewEmailResponse:
        """지원자에게 면접 안내 메일(면접 장소 지도 포함)을 발송한다."""
        company = self._get_or_create_company_for_user(user_id)

        application = self.application_repository.get_active_by_id_for_company(
            application_id, company.company_id
        )
        if application is None:
            raise CompanyApplicationNotFoundError

        applicant = self.user_repository.get_by_id(application.user_id)
        if applicant is None or not applicant.email:
            raise CompanyApplicationNotFoundError

        # 면접 장소: 요청에 명시한 주소 우선, 없으면 기업 등록 주소 사용.
        location_address = (
            payload.location_address or company.address or ""
        ).strip()
        if not location_address:
            raise InterviewLocationMissingError

        job = self.job_posting_repository.get_by_id(application.job_id)

        interview_email_service = InterviewEmailService()
        try:
            map_attached = interview_email_service.send_interview_invitation(
                to=applicant.email,
                applicant_name=applicant.name,
                company_name=company.company_name,
                job_title=job.title if job else None,
                location_address=location_address,
                interview_at=payload.interview_at,
                message=payload.message,
            )
        except (EmailConfigError, EmailSendError) as exc:
            raise InterviewEmailSendError from exc

        self.application_repository.update_status(
            application,
            status=APPLICATION_STATUS_INTERVIEW,
            actor_id=user_id,
            request_ip=request_ip,
        )
        self.db.commit()
        self.db.refresh(application)
        return InterviewEmailResponse(
            application_id=application.application_id,
            to_email=applicant.email,
            map_attached=map_attached,
            status=application.status,
            message="면접 안내 메일을 발송했습니다.",
        )

    def update_application_status(
        self,
        *,
        user_id: int,
        application_id: int,
        status: str,
        request_ip: str | None,
    ) -> CompanyApplicationStatusResponse:
        """기업이 받은 지원 상태를 수동 변경한다."""
        normalized = (status or "").strip().upper()
        if normalized not in COMPANY_MANUAL_APPLICATION_STATUSES:
            raise CompanyApplicationInvalidStatusError

        company = self._get_or_create_company_for_user(user_id)
        application = self.application_repository.get_active_by_id_for_company(
            application_id,
            company.company_id,
        )
        if application is None:
            raise CompanyApplicationNotFoundError

        self.application_repository.update_status(
            application,
            status=normalized,
            actor_id=user_id,
            request_ip=request_ip,
        )
        self.db.commit()
        self.db.refresh(application)
        return CompanyApplicationStatusResponse(
            application_id=application.application_id,
            status=application.status,
            message="지원 상태를 변경했습니다.",
        )

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

    def _ensure_match_scores_for_rows(
        self,
        rows,
        *,
        actor_id: int | None,
    ) -> dict[int, ApplicationMatchScoreResponse]:
        scores: dict[int, ApplicationMatchScoreResponse] = {}
        if not rows:
            return scores

        changed = False
        for row in rows:
            application = row.Application
            resume = self.resume_repository.get_by_id_no_user(application.resume_id)
            job = self.job_posting_repository.get_by_id(application.job_id)
            if resume is None or job is None:
                continue
            existing_score = (
                self.match_score_service.repository.get_by_application_id(
                    application.application_id
                )
            )
            existing_state = (
                (
                    existing_score.input_signature,
                    existing_score.model,
                    existing_score.algorithm_version,
                )
                if existing_score is not None
                else None
            )
            match_score = self.match_score_service.ensure_score_for_application(
                application,
                resume,
                job,
                actor_id=actor_id,
                request_ip=None,
            )
            if existing_state != (
                match_score.input_signature,
                match_score.model,
                match_score.algorithm_version,
            ):
                changed = True
            scores[application.application_id] = (
                ApplicationMatchScoreResponse.model_validate(match_score)
            )
        if changed:
            self.db.commit()
        return scores

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
