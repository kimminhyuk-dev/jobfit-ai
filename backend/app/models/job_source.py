"""
채용공고 수집원 모델
외부/수동 채용공고 수집원의 운영 상태를 관리한다.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class JobSource(Base, AuditMixin, SoftDeleteMixin):
    """채용공고 수집원 테이블."""

    __tablename__ = "job_sources"

    source_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="채용공고 수집원 PK",
    )
    source_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="수집원 코드 (ALIO/WORK24/SARAMIN/MANUAL)",
    )
    source_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="수집원 이름",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="ACTIVE/DISABLED/PENDING_APPROVAL/DEPRECATED",
    )
    disabled_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="비활성/보류 사유",
    )
    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="수집원 기본 URL",
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="마지막 상태 확인 시각",
    )

    def __repr__(self) -> str:
        return f"<JobSource(source_code={self.source_code}, status={self.status})>"
