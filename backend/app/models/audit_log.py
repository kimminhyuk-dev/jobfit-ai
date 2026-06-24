"""관리자 감사 로그 모델."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

AUDIT_ACTION_CREATE = "CREATE"
AUDIT_ACTION_UPDATE = "UPDATE"
AUDIT_ACTION_DELETE = "DELETE"

AUDIT_ACTION_VALUES = {
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_UPDATE,
    AUDIT_ACTION_DELETE,
}


class AuditLog(Base):
    """민감한 관리자 작업의 변경 이력을 저장한다."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="감사 로그 PK",
    )
    table_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
        comment="변경 대상 테이블",
    )
    record_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="변경 대상 레코드 식별값",
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="행위: CREATE/UPDATE/DELETE",
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="행위자 user_id",
    )
    actor_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="행위자 IP",
    )
    before_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="변경 전 값",
    )
    after_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="변경 후 값",
    )
    summary: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="변경 요약",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="기록 일시",
    )
