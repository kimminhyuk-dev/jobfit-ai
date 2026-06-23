"""관리자 휴가 신청/잔여일 모델."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin

LEAVE_TYPE_ANNUAL = "ANNUAL"
LEAVE_TYPE_AM_HALF = "AM_HALF"
LEAVE_TYPE_PM_HALF = "PM_HALF"
LEAVE_TYPE_SICK = "SICK"
LEAVE_TYPE_FAMILY_EVENT = "FAMILY_EVENT"
LEAVE_TYPE_OFFICIAL = "OFFICIAL"
LEAVE_TYPE_COMPENSATORY = "COMPENSATORY"

LEAVE_TYPE_VALUES = {
    LEAVE_TYPE_ANNUAL,
    LEAVE_TYPE_AM_HALF,
    LEAVE_TYPE_PM_HALF,
    LEAVE_TYPE_SICK,
    LEAVE_TYPE_FAMILY_EVENT,
    LEAVE_TYPE_OFFICIAL,
    LEAVE_TYPE_COMPENSATORY,
}

LEAVE_STATUS_PENDING = "PENDING"
LEAVE_STATUS_APPROVED = "APPROVED"
LEAVE_STATUS_REJECTED = "REJECTED"
LEAVE_STATUS_CANCELED = "CANCELED"
LEAVE_STATUS_CANCEL_REQUESTED = "CANCEL_REQUESTED"
LEAVE_STATUS_CHANGE_REQUESTED = "CHANGE_REQUESTED"

LEAVE_STATUS_VALUES = {
    LEAVE_STATUS_PENDING,
    LEAVE_STATUS_APPROVED,
    LEAVE_STATUS_REJECTED,
    LEAVE_STATUS_CANCELED,
    LEAVE_STATUS_CANCEL_REQUESTED,
    LEAVE_STATUS_CHANGE_REQUESTED,
}

HALF_DAY_AM = "AM"
HALF_DAY_PM = "PM"
HALF_DAY_VALUES = {HALF_DAY_AM, HALF_DAY_PM}

DEFAULT_GRANTED_DAYS = Decimal("15.00")


class LeaveBalance(Base, AuditMixin):
    """관리자별 연도별 휴가 잔여일."""

    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint("user_id", "year", name="uq_leave_balances_user_year"),
    )

    leave_balance_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="휴가 잔여 PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="관리자 user_id",
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="휴가 기준 연도",
    )
    granted_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
        comment="부여 일수",
    )
    used_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
        comment="사용 확정 일수",
    )
    pending_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
        comment="승인 대기 일수",
    )
    remaining_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
        comment="잔여 가능 일수",
    )

    def __repr__(self) -> str:
        return f"<LeaveBalance(user_id={self.user_id}, year={self.year})>"


class AdminLeaveRequest(Base, AuditMixin, SoftDeleteMixin):
    """관리자 휴가 신청."""

    __tablename__ = "admin_leave_requests"

    leave_request_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="휴가 신청 PK",
    )
    requester_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="신청자 user_id",
    )
    approver_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="결재 예정/담당자 user_id",
    )
    leave_balance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("leave_balances.leave_balance_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="연결된 휴가 잔여 PK",
    )
    leave_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="휴가 종류",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="휴가 시작일",
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="휴가 종료일",
    )
    start_half_day: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="시작일 반차 구분",
    )
    end_half_day: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="종료일 반차 구분",
    )
    requested_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        comment="신청 일수",
    )
    reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="신청 사유",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=LEAVE_STATUS_PENDING,
        server_default=LEAVE_STATUS_PENDING,
        index=True,
        comment="신청 상태",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="승인 시각",
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="반려 시각",
    )
    reject_reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="반려 사유",
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="취소 완료 시각",
    )
    cancel_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="취소 요청 시각",
    )
    change_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="일정 변경 요청 시각",
    )
    change_request_reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="일정 변경 요청 사유",
    )

    def __repr__(self) -> str:
        return (
            "<AdminLeaveRequest("
            f"leave_request_id={self.leave_request_id}, "
            f"requester_id={self.requester_id}, status={self.status})>"
        )
