"""
지원(이력서 보내기) 비즈니스 로직.

흐름:
1. 이력서가 본인 소유인지 확인
2. 공고가 존재하는지 확인
3. 공고 회사의 기업계정을 보장(이미 수집 시 생성되었으면 재사용)
4. 같은 공고 중복 지원 차단
5. 지원 레코드 생성 → 기업 대시보드의 지원현황에 노출
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.application import ApplicationResponse, MyApplicationItem
from app.services.company_provisioning_service import CompanyProvisioningService


class ApplicationResumeNotFoundError(Exception):
    """지원에 사용할 이력서를 찾을 수 없음."""


class ApplicationJobNotFoundError(Exception):
    """지원 대상 공고를 찾을 수 없음."""


class ApplicationAlreadyExistsError(Exception):
    """이미 같은 공고에 지원함."""


class ApplicationNotFoundError(Exception):
    """취소/조회할 지원 내역을 찾을 수 없음."""


class ApplicationService:
    """지원 관련 비즈니스 로직."""

    def __init__(self, db: Session):
        self.db = db
        self.application_repository = ApplicationRepository(db)
        self.job_posting_repository = JobPostingRepository(db)
        self.resume_repository = ResumeRepository(db)
        self.company_provisioning_service = CompanyProvisioningService(db)

    def apply(
        self,
        *,
        user_id: int,
        job_id: int,
        resume_id: int,
        request_ip: str | None,
    ) -> ApplicationResponse:
        resume = self.resume_repository.get_by_id(resume_id, user_id)
        if resume is None:
            raise ApplicationResumeNotFoundError

        job = self.job_posting_repository.get_by_id(job_id)
        if job is None:
            raise ApplicationJobNotFoundError

        if self.application_repository.get_active_by_user_job(user_id, job_id):
            raise ApplicationAlreadyExistsError

        # 이미 수집 시 생성된 기업계정이 있으면 재사용, 없으면 지금 보장한다.
        company = self.company_provisioning_service.ensure_company(
            company_name=job.company_name,
            business_number=job.business_number,
        )

        try:
            application = self.application_repository.create(
                user_id=user_id,
                job_id=job_id,
                resume_id=resume_id,
                company_id=company.company_id if company else None,
                actor_id=user_id,
                request_ip=request_ip,
            )
            self.db.commit()
        except IntegrityError as exc:
            # 부분 unique (user_id, job_id) 위반: 동시 중복 지원
            self.db.rollback()
            raise ApplicationAlreadyExistsError from exc

        self.db.refresh(application)
        return ApplicationResponse.model_validate(application)

    def list_my_applications(self, user_id: int) -> list[MyApplicationItem]:
        rows = self.application_repository.list_by_user(user_id)
        return [
            MyApplicationItem(
                application_id=row.Application.application_id,
                job_id=row.Application.job_id,
                job_title=row.job_title,
                company_name=row.company_name,
                source_url=row.source_url,
                resume_id=row.Application.resume_id,
                resume_title=row.resume_title,
                status=row.Application.status,
                applied_at=row.Application.applied_at,
                viewed_at=row.Application.viewed_at,
            )
            for row in rows
        ]

    def cancel_application(
        self,
        *,
        application_id: int,
        user_id: int,
        request_ip: str | None,
    ) -> None:
        """본인 지원을 취소(소프트 삭제)한다. 이후 같은 공고에 재지원할 수 있다."""
        application = self.application_repository.get_active_by_id_for_user(
            application_id, user_id
        )
        if application is None:
            raise ApplicationNotFoundError

        self.application_repository.cancel(
            application,
            actor_id=user_id,
            request_ip=request_ip,
        )
        self.db.commit()
