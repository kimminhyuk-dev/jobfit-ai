"""
User 모델
회원 정보를 담는 테이블
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class User(Base, AuditMixin, SoftDeleteMixin):
    """
    회원 테이블
    - 내부 PK: user_id (BIGINT, 자동증가)
    - 로그인 ID: email (UNIQUE)
    - 비밀번호: bcrypt 해시 저장 (평문 절대 금지)
    - 감사 컬럼: AuditMixin에서 상속
    - 소프트 삭제: SoftDeleteMixin에서 상속
    """

    __tablename__ = "users"

    # 기본 식별자
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="회원 내부 PK",
    )

    # 로그인 정보
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="로그인 ID (이메일)",
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="비밀번호 해시 (bcrypt)",
    )

    # 프로필
    name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="이름",
    )

    # 상태
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        comment="계정 상태: ACTIVE / LOCKED / DORMANT",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="USER",
        server_default="USER",
        comment="권한: USER / ADMIN",
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email})>"
