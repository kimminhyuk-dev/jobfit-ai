"""
EmailVerification 모델
이메일 인증 코드(비밀번호 재설정 등)를 단기 저장하는 테이블.

- Java JobFolio의 tb_email_verification 을 이식한 구조.
- 단, JobFolio는 인증 코드를 평문으로 저장하지만 여기서는 SHA-256 해시(code_hash)로
  저장한다(refresh_tokens 와 동일한 보안 컨벤션). 평문 코드는 메일로만 전달한다.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmailVerification(Base):
    """이메일 인증 코드 저장 테이블 (단기, 만료 기반)."""

    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="인증 대상 이메일",
    )
    purpose: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PASSWORD_RESET",
        server_default="PASSWORD_RESET",
        comment="용도: PASSWORD_RESET / SIGNUP 등",
    )
    code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="인증 코드의 SHA-256 해시 (평문 미저장)",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="만료 시각",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="사용(소비) 여부",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="사용 처리 시각",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="검증 실패 시도 횟수",
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="마지막 검증 시도 시각",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="발급 시각",
    )

    def __repr__(self) -> str:
        return f"<EmailVerification(id={self.id}, email={self.email}, purpose={self.purpose})>"
