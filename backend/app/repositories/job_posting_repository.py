"""
JobPosting 테이블 DB 접근 계층
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.job_posting import JobPosting


class JobPostingRepository:
    """채용공고 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_source(self, source: str, source_job_id: str) -> JobPosting | None:
        stmt = (
            select(JobPosting)
            .where(JobPosting.source == source)
            .where(JobPosting.source_job_id == source_job_id)
            .where(JobPosting.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        source: str,
        source_job_id: str,
        data: dict[str, Any],
    ) -> tuple[JobPosting, bool, bool]:
        """
        source/source_job_id 기준으로 INSERT 또는 UPDATE한다.

        반환값:
        - JobPosting
        - 신규 INSERT 여부
        - hash_signature 동일로 본문 업데이트를 건너뛴 여부
        """
        posting = self.get_by_source(source=source, source_job_id=source_job_id)
        now = datetime.now(timezone.utc)

        if posting is None:
            posting = JobPosting(
                source=source,
                source_job_id=source_job_id,
                last_checked_at=now,
                **data,
            )
            self.db.add(posting)
            self.db.flush()
            return posting, True, False

        if posting.hash_signature == data.get("hash_signature"):
            posting.last_checked_at = now
            posting.collect_run_id = data.get("collect_run_id")
            self.db.flush()
            return posting, False, True

        for field, value in data.items():
            setattr(posting, field, value)
        posting.last_checked_at = now
        self.db.flush()
        return posting, False, False

    def list_by_filter(
        self,
        page: int,
        size: int,
        filters: dict[str, Any],
    ) -> tuple[list[JobPosting], int]:
        """저장된 채용공고를 조건별로 조회한다."""
        conditions = [JobPosting.is_deleted.is_(False)]

        source = _clean(filters.get("source"))
        if source:
            conditions.append(JobPosting.source == source)

        keyword = _clean(filters.get("keyword"))
        if keyword:
            pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    JobPosting.title.ilike(pattern),
                    JobPosting.company_name.ilike(pattern),
                    JobPosting.raw_content.ilike(pattern),
                )
            )

        for field_name in (
            "location_code",
            "employment_type_code",
            "education_code",
            "career_level_code",
            "status",
        ):
            value = _clean(filters.get(field_name))
            if value:
                conditions.append(getattr(JobPosting, field_name) == value)

        total_stmt = select(func.count()).select_from(JobPosting).where(*conditions)
        total = int(self.db.execute(total_stmt).scalar_one())

        stmt = (
            select(JobPosting)
            .where(*conditions)
            .order_by(JobPosting.deadline.asc().nulls_last(), JobPosting.job_id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        postings = list(self.db.execute(stmt).scalars().all())
        return postings, total

    def count_all(self) -> int:
        stmt = select(func.count()).select_from(JobPosting)
        return int(self.db.execute(stmt).scalar_one())


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
