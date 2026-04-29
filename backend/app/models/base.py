"""
모든 모델이 공통으로 상속할 Mixin 클래스
- AuditMixin: 감사 컬럼 (누가 언제 어디서 생성/수정했는지)
- SoftDeleteMixin: 소프트 삭제 플래그
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    """
    감사(Audit) 컬럼 Mixin
    모든 테이블에 "누가 언제 어디서" 기록을 강제

    사용 예:
        class User(Base, AuditMixin):
            ...
    """

    # 생성 정보
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="생성자 user_id (회원가입 시에는 null)",
    )
    created_ip: Mapped[str | None] = mapped_column(
        String(45),  # IPv6까지 수용 (39자) + 여유
        nullable=True,
        comment="생성 요청 IP",
    )

    # 수정 정보
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="최종 수정 시각",
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="최종 수정자 user_id",
    )
    updated_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="최종 수정 요청 IP",
    )


class SoftDeleteMixin:
    """
    소프트 삭제 Mixin
    실제 DELETE 대신 is_deleted=True로 마킹
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="삭제 여부 (소프트 삭제)",
    )
