"""관리자 휴가 신청/결재 요청·응답 스키마."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.admin_leave import (
    HALF_DAY_VALUES,
    LEAVE_STATUS_APPROVED,
    LEAVE_STATUS_CANCELED,
    LEAVE_STATUS_CANCEL_REQUESTED,
    LEAVE_STATUS_CHANGE_REQUESTED,
    LEAVE_STATUS_PENDING,
    LEAVE_STATUS_REJECTED,
    LEAVE_TYPE_AM_HALF,
    LEAVE_TYPE_ANNUAL,
    LEAVE_TYPE_COMPENSATORY,
    LEAVE_TYPE_FAMILY_EVENT,
    LEAVE_TYPE_OFFICIAL,
    LEAVE_TYPE_PM_HALF,
    LEAVE_TYPE_SICK,
)

LeaveType = Literal[
    "ANNUAL",
    "AM_HALF",
    "PM_HALF",
    "SICK",
    "FAMILY_EVENT",
    "OFFICIAL",
    "COMPENSATORY",
]

LeaveStatus = Literal[
    "PENDING",
    "APPROVED",
    "REJECTED",
    "CANCELED",
    "CANCEL_REQUESTED",
    "CHANGE_REQUESTED",
]


class LeaveBalanceResponse(BaseModel):
    """휴가 잔여일 응답."""

    model_config = ConfigDict(from_attributes=True)

    leave_balance_id: int
    user_id: int
    year: int
    granted_days: Decimal
    used_days: Decimal
    pending_days: Decimal
    remaining_days: Decimal


class AdminLeaveRequestCreate(BaseModel):
    """휴가 신청 요청."""

    leave_type: LeaveType
    start_date: date
    end_date: date
    start_half_day: str | None = None
    end_half_day: str | None = None
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("leave_type", mode="before")
    @classmethod
    def normalize_leave_type(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("start_half_day", "end_half_day", mode="before")
    @classmethod
    def normalize_half_day(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        normalized = value.strip().upper()
        if normalized not in HALF_DAY_VALUES:
            raise ValueError("반차 구분은 AM 또는 PM만 사용할 수 있습니다.")
        return normalized

    @model_validator(mode="after")
    def validate_dates(self) -> "AdminLeaveRequestCreate":
        if self.start_date > self.end_date:
            raise ValueError("휴가 시작일은 종료일보다 늦을 수 없습니다.")
        if self.leave_type in {LEAVE_TYPE_AM_HALF, LEAVE_TYPE_PM_HALF}:
            if self.start_date != self.end_date:
                raise ValueError("반차는 하루 단위로만 신청할 수 있습니다.")
        return self


class AdminLeaveRejectRequest(BaseModel):
    """휴가 반려 요청."""

    reject_reason: str = Field(min_length=1, max_length=1000)

    @field_validator("reject_reason")
    @classmethod
    def strip_reject_reason(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("반려 사유를 입력해 주세요.")
        return stripped


class AdminLeaveChangeRequest(BaseModel):
    """휴가 일정 변경 요청(결재자가 승인/반려 대신 일정 수정을 요청)."""

    change_reason: str = Field(min_length=1, max_length=1000)

    @field_validator("change_reason")
    @classmethod
    def strip_change_reason(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("변경 요청 사유를 입력해 주세요.")
        return stripped


class AdminLeaveRequestResponse(BaseModel):
    """휴가 신청 응답."""

    model_config = ConfigDict(from_attributes=True)

    leave_request_id: int
    requester_id: int
    requester_name: str | None = None
    requester_email: str | None = None
    approver_id: int | None
    approver_name: str | None = None
    approver_email: str | None = None
    leave_balance_id: int | None
    leave_type: LeaveType
    start_date: date
    end_date: date
    start_half_day: str | None
    end_half_day: str | None
    requested_days: Decimal
    reason: str | None
    status: LeaveStatus
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    reject_reason: str | None = None
    canceled_at: datetime | None = None
    cancel_requested_at: datetime | None = None
    change_requested_at: datetime | None = None
    change_request_reason: str | None = None
    created_at: datetime
    updated_at: datetime


LEAVE_TYPE_LABELS = {
    LEAVE_TYPE_ANNUAL: "연차",
    LEAVE_TYPE_AM_HALF: "오전반차",
    LEAVE_TYPE_PM_HALF: "오후반차",
    LEAVE_TYPE_SICK: "병가",
    LEAVE_TYPE_FAMILY_EVENT: "경조휴가",
    LEAVE_TYPE_OFFICIAL: "공가",
    LEAVE_TYPE_COMPENSATORY: "대체휴무",
}

LEAVE_STATUS_LABELS = {
    LEAVE_STATUS_PENDING: "신청 대기",
    LEAVE_STATUS_APPROVED: "승인",
    LEAVE_STATUS_REJECTED: "반려",
    LEAVE_STATUS_CANCELED: "취소",
    LEAVE_STATUS_CANCEL_REQUESTED: "취소 요청",
    LEAVE_STATUS_CHANGE_REQUESTED: "일정 변경 요청",
}
