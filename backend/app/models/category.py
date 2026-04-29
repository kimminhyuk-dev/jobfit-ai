"""
Category 모델
Q&A 게시판 카테고리 정보를 담는 테이블
"""

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Category(Base, AuditMixin, SoftDeleteMixin):
    """
    게시판 카테고리 테이블
    - slug는 URL/필터용 고유 키로 사용
    - is_active=False면 일반 사용자 조회에서 제외
    """

    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="카테고리 PK",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="카테고리 이름",
    )
    slug: Mapped[str] = mapped_column(
        String(60),
        unique=True,
        nullable=False,
        index=True,
        comment="카테고리 고유 슬러그",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="카테고리 설명",
    )
    sort_order: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="노출 순서",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="활성 여부",
    )

    def __repr__(self) -> str:
        return f"<Category(category_id={self.category_id}, slug={self.slug})>"
