"""
Application 테이블 DB 접근 계층
"""

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
            .where(Application.is_deleted.is_(False))
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
