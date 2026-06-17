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

    def get_by_id(self, job_id: int) -> JobPosting | None:
        stmt = (
            select(JobPosting)
            .where(JobPosting.job_id == job_id)
            .where(JobPosting.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

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

        status_value = _clean(filters.get("status"))
        if status_value:
            conditions.append(JobPosting.status == status_value)
        else:
            conditions.append(JobPosting.status != "HIDDEN")

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
            "data_source",
        ):
            value = _clean(filters.get(field_name))
            if value:
                conditions.append(getattr(JobPosting, field_name) == value)

        # 텍스트 기반 필터 (사람인/잡코리아식 지역·학력·직종 선택)
        region = _clean(filters.get("region"))
        if region:
            conditions.append(JobPosting.location.ilike(f"{region}%"))
        education = _clean(filters.get("education"))
        if education:
            conditions.append(JobPosting.education.ilike(f"%{education}%"))
        employment_type = _clean(filters.get("employment_type"))
        if employment_type:
            conditions.append(JobPosting.employment_type.ilike(f"%{employment_type}%"))
        ncs_category = _clean(filters.get("ncs_category"))
        if ncs_category:
            conditions.append(JobPosting.ncs_category.ilike(f"%{ncs_category}%"))

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

    def filter_options(self) -> dict[str, list[str]]:
        """실제 공고 데이터에서 지역/학력/고용형태/직종 선택지를 추출한다."""

        def raw_distinct(column) -> list[str]:
            stmt = (
                select(column, func.count())
                .where(JobPosting.is_deleted.is_(False))
                .where(column.isnot(None))
                .group_by(column)
                .order_by(func.count().desc())
            )
            return [v for v, _ in self.db.execute(stmt).all() if v and v.strip()]

        def atomic(values: list[str], sep: str = ",") -> list[str]:
            ordered: list[str] = []
            for value in values:
                for part in value.split(sep):
                    token = part.strip()
                    if token and token not in ordered:
                        ordered.append(token)
            return ordered

        regions: list[str] = []
        for location in raw_distinct(JobPosting.location):
            head = location.split()[0].strip()
            if head and head not in regions:
                regions.append(head)

        return {
            "regions": regions,
            "educations": atomic(raw_distinct(JobPosting.education)),
            "employment_types": atomic(raw_distinct(JobPosting.employment_type)),
            "job_categories": atomic(raw_distinct(JobPosting.ncs_category)),
        }

    def count_by_company(
        self,
        business_number: str | None,
        company_name: str | None,
    ) -> int:
        """기업의 사업자번호/회사명과 일치하는 등록 공고 수를 센다."""
        identifiers = self._company_identifiers(business_number, company_name)
        if not identifiers:
            return 0
        stmt = (
            select(func.count())
            .select_from(JobPosting)
            .where(JobPosting.is_deleted.is_(False))
            .where(or_(*identifiers))
        )
        return int(self.db.execute(stmt).scalar_one())

    def list_by_company(
        self,
        business_number: str | None,
        company_name: str | None,
    ) -> list[JobPosting]:
        """기업의 사업자번호/회사명과 일치하는 공고를 최신순으로 조회한다."""
        identifiers = self._company_identifiers(business_number, company_name)
        if not identifiers:
            return []
        stmt = (
            select(JobPosting)
            .where(JobPosting.is_deleted.is_(False))
            .where(or_(*identifiers))
            .order_by(JobPosting.created_at.desc(), JobPosting.job_id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_company_owned(
        self,
        job_id: int,
        business_number: str | None,
        company_name: str | None,
    ) -> JobPosting | None:
        """기업에 속한(사업자번호/회사명 일치) 단일 공고를 조회한다."""
        identifiers = self._company_identifiers(business_number, company_name)
        if not identifiers:
            return None
        stmt = (
            select(JobPosting)
            .where(JobPosting.job_id == job_id)
            .where(JobPosting.is_deleted.is_(False))
            .where(or_(*identifiers))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_company_job(
        self,
        *,
        company_name: str | None,
        business_number: str | None,
        fields: dict[str, Any],
        actor_id: int,
        request_ip: str | None,
    ) -> JobPosting:
        """기업이 직접 등록하는 MANUAL 공고를 생성한다."""
        posting = JobPosting(
            source="MANUAL",
            source_job_id=None,
            data_source="MANUAL",
            company_name=company_name,
            business_number=business_number,
            posted_at=datetime.now(timezone.utc),
            collected_at=datetime.now(timezone.utc),
            created_by=actor_id,
            created_ip=request_ip,
            updated_by=actor_id,
            updated_ip=request_ip,
            **fields,
        )
        self.db.add(posting)
        self.db.flush()
        return posting

    def update_fields(
        self,
        posting: JobPosting,
        fields: dict[str, Any],
        actor_id: int,
        request_ip: str | None,
    ) -> JobPosting:
        for key, value in fields.items():
            setattr(posting, key, value)
        posting.updated_by = actor_id
        posting.updated_ip = request_ip
        self.db.flush()
        return posting

    def soft_delete(
        self,
        posting: JobPosting,
        actor_id: int,
        request_ip: str | None,
    ) -> None:
        posting.is_deleted = True
        posting.status = "CLOSED"
        posting.updated_by = actor_id
        posting.updated_ip = request_ip
        self.db.flush()

    @staticmethod
    def _company_identifiers(
        business_number: str | None,
        company_name: str | None,
    ) -> list[Any]:
        identifiers: list[Any] = []
        if business_number:
            identifiers.append(JobPosting.business_number == business_number)
        if company_name:
            identifiers.append(JobPosting.company_name == company_name)
        return identifiers


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
