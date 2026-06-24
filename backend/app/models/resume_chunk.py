"""
이력서 청크 모델
이력서 섹션별 텍스트와 OpenAI 임베딩 벡터를 저장한다.
"""

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, RegModAuditMixin


class ResumeChunk(Base, AuditMixin, RegModAuditMixin):
    """이력서 섹션 청크 테이블"""

    __tablename__ = "resume_chunks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="이력서 청크 PK",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="부모 이력서 PK",
    )
    section: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="청크 섹션 라벨",
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="이력서 내 청크 순번",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="청크 텍스트",
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536),
        nullable=False,
        comment="text-embedding-3-small 1536차원 임베딩",
    )

    def __repr__(self) -> str:
        return (
            f"<ResumeChunk(id={self.id}, resume_id={self.resume_id}, "
            f"section={self.section!r}, chunk_index={self.chunk_index})>"
        )

    def to_summary(self) -> dict[str, Any]:
        """검증과 응답 생성에 쓰는 최소 정보를 반환한다."""

        return {
            "id": self.id,
            "resume_id": self.resume_id,
            "section": self.section,
            "chunk_index": self.chunk_index,
        }
