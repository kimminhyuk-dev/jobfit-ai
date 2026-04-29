"""
Post 모델
간단한 게시글 정보를 담는 테이블
"""

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Post(Base, AuditMixin, SoftDeleteMixin):
    """
    게시글 테이블
    - 작성자: users.user_id 참조
    - 카테고리: categories.category_id 참조
    - 목록/상세 조회와 기본 CRUD 용도
    """

    __tablename__ = "posts"

    post_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="게시글 PK",
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="작성자 user_id",
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.category_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="카테고리 PK",
    )
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="제목",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="본문",
    )

    def __repr__(self) -> str:
        return f"<Post(post_id={self.post_id}, author_id={self.author_id})>"
