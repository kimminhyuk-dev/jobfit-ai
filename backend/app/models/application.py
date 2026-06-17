"""
Application 모델
지원자가 공고에 이력서를 보낸 지원 내역을 담는 테이블.

- user(지원자)가 job_posting에 resume를 선택해 지원한다.
- 지원 레코드는 해당 공고의 기업계정(company)에 노출되어 지원현황을 구성한다.
- 같은 공고에 중복 지원은 막는다(부분 unique 인덱스).
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Application(Base, AuditMixin, SoftDeleteMixin):
    """지원(이력서 보내기) 테이블."""

    __tablename__ = "applications"
    __table_args__ = (
        Index(
            "uq_applications_user_job",
            "user_id",
            "job_id",
            unique=True,
            postgresql_where=text("is_deleted IS FALSE"),
        ),
    )

    application_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="지원 PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="지원자 user_id",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="지원에 사용한 이력서 resume_id",
    )
    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("job_postings.job_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="지원한 공고 job_id",
    )
    company_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("companies.company_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="지원이 전달되는 기업계정 company_id",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SUBMITTED",
        server_default="SUBMITTED",
        index=True,
        comment="지원 상태: SUBMITTED / VIEWED / ACCEPTED / REJECTED / CANCELED",
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="지원 시각",
    )
    viewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="기업이 이력서를 처음 열람한 시각 (미열람이면 null)",
    )

    def __repr__(self) -> str:
        return f"<Application(application_id={self.application_id}, user_id={self.user_id}, job_id={self.job_id})>"
