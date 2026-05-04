"""
Resume 모델
사용자가 업로드한 이력서 원본과 규칙 기반 파싱 결과를 저장한다.
"""

from sqlalchemy import BigInteger, ForeignKey, Index, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Resume(Base, AuditMixin, SoftDeleteMixin):
    """사용자 이력서 테이블"""

    __tablename__ = "resumes"
    __table_args__ = (
        Index(
            "uq_resumes_one_default_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_default IS TRUE AND is_deleted IS FALSE"),
        ),
    )

    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="이력서 PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="소유자 user_id",
    )
    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        comment="이력서 제목",
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="사용자가 업로드한 원본 파일명",
    )
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="서버 저장 파일명",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="서버 저장 경로",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="파일 크기(byte)",
    )
    content_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        comment="업로드 Content-Type",
    )
    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="파일에서 추출한 원문 텍스트",
    )
    parsed_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="규칙 기반 파싱 결과 JSON",
    )
    parse_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
        comment="파싱 상태: PENDING / COMPLETED / FAILED",
    )
    parse_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="파싱 실패 메시지",
    )
    is_default: Mapped[bool] = mapped_column(
        default=False,
        server_default="false",
        nullable=False,
        comment="기본 이력서 여부",
    )

    def __repr__(self) -> str:
        return f"<Resume(resume_id={self.resume_id}, user_id={self.user_id})>"
