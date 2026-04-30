"""
공통코드 모델
ALIO 코드 정의서 기반 코드 그룹과 상세 코드를 관리한다.
"""

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class CommonCodeGroup(Base, AuditMixin, SoftDeleteMixin):
    """공통코드 그룹 테이블."""

    __tablename__ = "common_code_groups"
    __table_args__ = (
        UniqueConstraint(
            "category_code",
            "code_group",
            name="uq_common_code_groups_category_group",
        ),
        UniqueConstraint("code_group", name="uq_common_code_groups_code_group"),
    )

    group_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="공통코드 그룹 PK",
    )
    category_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="대분류 코드 (REC/INST 등)",
    )
    code_group: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="코드 그룹 (R1000/A2000 등)",
    )
    code_group_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="코드 그룹명",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="설명",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="활성 여부",
    )


class CommonCode(Base, AuditMixin, SoftDeleteMixin):
    """공통상세코드 테이블."""

    __tablename__ = "common_codes"
    __table_args__ = (
        UniqueConstraint("code_group", "code", name="uq_common_codes_group_code"),
    )

    code_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="공통상세코드 PK",
    )
    code_group: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("common_code_groups.code_group"),
        nullable=False,
        index=True,
        comment="코드 그룹",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="상세 코드",
    )
    code_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="코드명",
    )
    code_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="코드 설명",
    )
    parent_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="상위 코드",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="정렬 순서",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="활성 여부",
    )
