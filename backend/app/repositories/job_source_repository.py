"""
JobSource 테이블 DB 접근 계층
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_source import JobSource


class JobSourceRepository:
    """채용공고 수집원 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, source_code: str) -> JobSource | None:
        stmt = (
            select(JobSource)
            .where(JobSource.source_code == source_code)
            .where(JobSource.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()
