"""
이력서 자기소개서 목차 구조화 모델
파싱된 자기소개서 소제목(성장과정, 지원동기 등)을 행 단위로 저장한다.
"""

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class ResumeCoverLetterSection(Base, AuditMixin):
    """이력서 자기소개서 목차 구조화 테이블 — resume당 여러 행"""

    __tablename__ = "resume_cover_letter_sections"

    section_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="자기소개서 목차 PK",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="부모 이력서 PK",
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="표시 순서 (0부터 시작)",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="소제목 (예: 성장과정, 지원동기)",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="소제목별 내용",
    )

    def __repr__(self) -> str:
        return f"<ResumeCoverLetterSection(section_id={self.section_id}, resume_id={self.resume_id}, title={self.title!r})>"
