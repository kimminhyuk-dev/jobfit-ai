"""
JobPosting 모델
외부 채용공고 원본과 파싱 정보를 담는 테이블
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class JobPosting(Base, AuditMixin, SoftDeleteMixin):
    """
    채용공고 테이블
    - source/source_job_id 조합으로 외부 공고를 식별
    - Work24 XML 응답은 dict 변환 후 raw_response에 보관
    """

    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint("source", "source_job_id", name="uq_job_postings_source"),
    )

    job_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="채용공고 PK",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="공고 출처 (WORK24/SARAMIN/MANUAL)",
    )
    source_job_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="외부 공고 ID (Work24의 wantedAuthNo)",
    )
    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="원문 URL (wantedInfoUrl)",
    )
    mobile_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="모바일 URL (wantedMobileInfoUrl)",
    )

    company_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="회사명",
    )
    business_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="사업자등록번호",
    )
    industry: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="업종",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="채용제목",
    )

    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="근무지역 텍스트",
    )
    location_address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="근무지 전체주소",
    )
    career_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="경력조건 텍스트",
    )
    min_career_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_career_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="학력조건",
    )
    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="고용형태",
    )
    employment_type_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    work_schedule: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="근무시간/형태",
    )

    salary_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="임금형태 (D/H/M/Y)",
    )
    salary_text: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="급여 원문",
    )
    min_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="등록일자",
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="마감일/접수마감일",
    )
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="외부 API 최종수정일 (smodifyDtm)",
    )

    raw_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="직무내용 + 기타 안내 텍스트 통합본",
    )
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="외부 API 원본 응답 (XML->dict 변환)",
    )
    parsed_skills: Mapped[list[str] | dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="추출된 스킬/키워드 리스트",
    )
    hash_signature: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="변경 감지용 SHA256",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
        index=True,
        comment="공고 상태 (OPEN/CLOSED/EXPIRED/HIDDEN)",
    )
    collection_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="COLLECTED",
        server_default="COLLECTED",
        comment="수집/후처리 상태 (COLLECTED/PARSED/EMBEDDED/FAILED)",
    )
    embedding_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        comment="임베딩 처리 상태 (PENDING/COMPLETED/FAILED)",
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="수집 시각",
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    collect_run_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("batch_job_runs.run_id"),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<JobPosting(job_id={self.job_id}, source={self.source})>"
