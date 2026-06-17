"""
Application 테이블 DB 접근 계층
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job_posting import JobPosting
from app.models.resume import Resume
from app.models.user import User


class ApplicationRepository:
    """지원 내역 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_by_user_job(self, user_id: int, job_id: int) -> Application | None:
        """같은 공고에 대한 (삭제되지 않은) 기존 지원을 조회한다."""
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .where(Application.job_id == job_id)
            .where(Application.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_by_id_for_user(
        self, application_id: int, user_id: int
    ) -> Application | None:
        """지원 취소를 위해 본인 소유의 (삭제되지 않은) 지원을 조회한다."""
        stmt = (
            select(Application)
            .where(Application.application_id == application_id)
            .where(Application.user_id == user_id)
            .where(Application.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_by_id_for_company(
        self, application_id: int, company_id: int
    ) -> Application | None:
        """기업 열람을 위해 해당 기업에 전달된 (삭제되지 않은) 지원을 조회한다."""
        stmt = (
            select(Application)
            .where(Application.application_id == application_id)
            .where(Application.company_id == company_id)
            .where(Application.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def cancel(
        self, application: Application, *, actor_id: int, request_ip: str | None
    ) -> None:
        """지원 취소 상태를 남기고, 같은 공고 재지원은 가능하게 비활성 처리한다."""
        application.status = "CANCELED"
        application.is_deleted = True
        application.updated_by = actor_id
        application.updated_ip = request_ip
        self.db.flush()

    def mark_viewed(
        self, application: Application, *, actor_id: int, request_ip: str | None
    ) -> Application:
        """기업이 이력서를 처음 열람하면 상태를 VIEWED로 바꾸고 열람 시각을 기록한다."""
        if application.status == "SUBMITTED":
            application.status = "VIEWED"
            application.viewed_at = datetime.now(timezone.utc)
            application.updated_by = actor_id
            application.updated_ip = request_ip
            self.db.flush()
        return application

    def create(
        self,
        *,
        user_id: int,
        job_id: int,
        resume_id: int,
        company_id: int | None,
        actor_id: int,
        request_ip: str | None,
    ) -> Application:
        application = Application(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
            company_id=company_id,
            status="SUBMITTED",
            created_by=actor_id,
            created_ip=request_ip,
            updated_by=actor_id,
            updated_ip=request_ip,
        )
        self.db.add(application)
        self.db.flush()
        return application

    def list_by_user(self, user_id: int) -> list[Row[Any]]:
        """내 지원현황을 공고·이력서 정보와 함께 최신순으로 조회한다."""
        stmt = (
            select(
                Application,
                JobPosting.title.label("job_title"),
                JobPosting.company_name.label("company_name"),
                JobPosting.source_url.label("source_url"),
                Resume.title.label("resume_title"),
            )
            .join(JobPosting, JobPosting.job_id == Application.job_id)
            .join(Resume, Resume.resume_id == Application.resume_id)
            .where(Application.user_id == user_id)
            .where(
                (Application.is_deleted.is_(False))
                | (Application.status == "CANCELED")
            )
            .order_by(Application.applied_at.desc())
        )
        return list(self.db.execute(stmt).all())

    def count_by_user(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id)
            .where(Application.is_deleted.is_(False))
        )
        return int(self.db.execute(stmt).scalar_one())

    def list_by_company(self, company_id: int) -> list[Row[Any]]:
        """기업이 받은 지원(지원자 현황)을 최신순으로 조회한다."""
        stmt = (
            select(
                Application,
                User.name.label("applicant_name"),
                User.email.label("applicant_email"),
                JobPosting.title.label("job_title"),
                Resume.title.label("resume_title"),
            )
            .join(User, User.user_id == Application.user_id)
            .join(JobPosting, JobPosting.job_id == Application.job_id)
            .join(Resume, Resume.resume_id == Application.resume_id)
            .where(Application.company_id == company_id)
            .where(Application.is_deleted.is_(False))
            .order_by(Application.applied_at.desc())
        )
        return list(self.db.execute(stmt).all())

    def count_by_company(self, company_id: int) -> tuple[int, int]:
        """(전체 지원 수, 열람 대기=SUBMITTED 수)를 반환한다."""
        base = (
            select(func.count())
            .select_from(Application)
            .where(Application.company_id == company_id)
            .where(Application.is_deleted.is_(False))
        )
        total = int(self.db.execute(base).scalar_one())
        pending = int(
            self.db.execute(base.where(Application.status == "SUBMITTED")).scalar_one()
        )
        return total, pending

    def count_active_by_company_jobs(self, company_id: int) -> dict[int, int]:
        """기업의 공고별 (삭제되지 않은) 지원 수를 {job_id: count}로 반환한다."""
        stmt = (
            select(Application.job_id, func.count())
            .where(Application.company_id == company_id)
            .where(Application.is_deleted.is_(False))
            .group_by(Application.job_id)
        )
        return {job_id: int(count) for job_id, count in self.db.execute(stmt).all()}
