"""
이력서 구조화 프로젝트 모델
파싱된 개별 프로젝트를 행 단위로 저장한다.
"""

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class ResumeProject(Base, AuditMixin):
    """이력서 프로젝트 구조화 테이블 — resume당 여러 행"""

    __tablename__ = "resume_projects"

    project_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="프로젝트 PK",
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
    name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="프로젝트명",
    )
    period: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="수행 기간 (예: 2023.01 - 2023.06)",
    )
    role: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="맡은 역할",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="프로젝트 내용 · 설명",
    )
    review: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="후기 · 배운 점",
    )
    tech_stack: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="사용 기술 목록 (문자열 배열)",
    )
    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="파싱 전 원문 블록",
    )

    def __repr__(self) -> str:
        return f"<ResumeProject(project_id={self.project_id}, resume_id={self.resume_id}, name={self.name!r})>"
