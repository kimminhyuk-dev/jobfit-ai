"""
BatchJobRun 모델
외부 수집/후처리 배치 실행 이력을 담는 테이블
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class BatchJobRun(Base, AuditMixin, SoftDeleteMixin):
    """
    배치 실행 이력 테이블
    - Work24 수집, 마감 동기화, 임베딩 등 비동기 작업 추적
    - idempotency_key로 중복 실행을 방지
    """

    __tablename__ = "batch_job_runs"

    run_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="배치 실행 PK",
    )
    job_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="배치 코드 (WORK24_COLLECT/JOB_CLOSE_SYNC/JOB_EMBEDDING 등)",
    )
    job_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="배치 이름",
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="중복 실행 방지용 키",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="READY",
        server_default="READY",
        index=True,
        comment="READY/RUNNING/SUCCESS/FAILED/PARTIAL_SUCCESS/SKIPPED/RATE_LIMITED",
    )
    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="MANUAL/SCHEDULED/RETRY",
    )
    triggered_by: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="관리자 user_id 또는 SYSTEM",
    )

    request_params: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="실행 시 keyword, startPage, display, region, occupation 등",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    collected_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    inserted_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    updated_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    skipped_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    error_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<BatchJobRun(run_id={self.run_id}, job_code={self.job_code})>"
