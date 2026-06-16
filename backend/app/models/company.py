"""
Company 모델
기업회원 계정과 회사 식별 정보를 담는 테이블.

- 크롤링 공고 수집 시점에 회사별로 1계정을 생성한다.
- 같은 회사 판별은 사업자번호 우선, 없으면 회사명으로 한다(dedup_key).
- 로그인 계정은 users 테이블(role=COMPANY)과 1:1로 연결된다.
"""

from sqlalchemy import BigInteger, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class Company(Base, AuditMixin, SoftDeleteMixin):
    """기업회원(회사) 테이블."""

    __tablename__ = "companies"
    __table_args__ = (
        Index(
            "uq_companies_dedup_key",
            "dedup_key",
            unique=True,
            postgresql_where=text("is_deleted IS FALSE"),
        ),
    )

    company_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="기업 PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="로그인 계정 user_id (role=COMPANY)",
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
        index=True,
        comment="사업자등록번호",
    )
    dedup_key: Mapped[str] = mapped_column(
        String(220),
        nullable=False,
        comment="회사 식별 키 (bn:{사업자번호} 우선, 없으면 nm:{회사명})",
    )

    def __repr__(self) -> str:
        return f"<Company(company_id={self.company_id}, dedup_key={self.dedup_key})>"
