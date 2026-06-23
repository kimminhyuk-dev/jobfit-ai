"""관리자 휴가 신청/결재 비즈니스 로직."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.admin_leave import (
    AdminLeaveRequest,
    DEFAULT_GRANTED_DAYS,
    LEAVE_STATUS_APPROVED,
    LEAVE_STATUS_CANCELED,
    LEAVE_STATUS_CANCEL_REQUESTED,
    LEAVE_STATUS_CHANGE_REQUESTED,
    LEAVE_STATUS_PENDING,
    LEAVE_STATUS_REJECTED,
    LEAVE_TYPE_AM_HALF,
    LEAVE_TYPE_PM_HALF,
)
from app.models.team import TEAM_ROLE_LEAD, TEAM_ROLE_MEMBER
from app.models.user import User
from app.repositories.admin_leave_repository import AdminLeaveRepository
from app.schemas.admin_leave import (
    AdminLeaveChangeRequest,
    AdminLeaveRejectRequest,
    AdminLeaveRequestCreate,
    AdminLeaveRequestResponse,
)

DECIMAL_STEP = Decimal("0.01")
HALF_DAY = Decimal("0.50")


class LeaveInvalidRequestError(Exception):
    """휴가 신청 입력 또는 결재선이 올바르지 않음."""


class LeaveApproverNotFoundError(Exception):
    """휴가 결재자를 찾을 수 없음."""


class LeaveInsufficientBalanceError(Exception):
    """휴가 잔여일이 부족함."""


class LeaveRequestNotFoundError(Exception):
    """휴가 신청을 찾을 수 없음."""


class LeaveForbiddenError(Exception):
    """휴가 신청/결재 권한 범위가 아님."""


class LeaveInvalidStatusError(Exception):
    """현재 상태에서 요청한 처리를 할 수 없음."""


class AdminLeaveService:
    """관리자 휴가 신청/결재 서비스."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AdminLeaveRepository(db)

    def create_request(
        self,
        *,
        requester: User,
        payload: AdminLeaveRequestCreate,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """휴가를 신청하고 잔여일의 대기 일수를 늘린다."""
        requested_days = self._calculate_requested_days(payload)
        approver = self._determine_approver(requester)
        if approver.user_id == requester.user_id:
            raise LeaveForbiddenError

        balance = self._get_or_create_balance(
            user_id=requester.user_id,
            year=payload.start_date.year,
            actor_id=requester.user_id,
            request_ip=request_ip,
        )
        if self._decimal(balance.remaining_days) < requested_days:
            raise LeaveInsufficientBalanceError

        balance.pending_days = self._decimal(balance.pending_days) + requested_days
        balance.remaining_days = self._decimal(balance.remaining_days) - requested_days
        self._touch(balance, requester.user_id, request_ip)

        start_half_day, end_half_day = self._resolve_half_days(payload)

        leave_request = self.repository.create_request(
            requester_id=requester.user_id,
            approver_id=approver.user_id,
            leave_balance_id=balance.leave_balance_id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            start_half_day=start_half_day,
            end_half_day=end_half_day,
            requested_days=requested_days,
            reason=payload.reason.strip() if payload.reason else None,
            actor_id=requester.user_id,
            request_ip=request_ip,
        )
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def list_my_requests(self, requester_id: int) -> list[AdminLeaveRequestResponse]:
        """내 휴가 신청 목록을 조회한다."""
        return self._to_responses(self.repository.list_by_requester(requester_id))

    def list_pending_approvals(self, approver_id: int) -> list[AdminLeaveRequestResponse]:
        """내가 결재해야 할 휴가 신청 목록을 조회한다."""
        return self._to_responses(self.repository.list_pending_for_approver(approver_id))

    def approve_request(
        self,
        *,
        leave_request_id: int,
        approver: User,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """휴가 신청을 승인한다."""
        leave_request = self._get_request_or_raise(leave_request_id)
        self._ensure_assigned_approver(leave_request, approver.user_id)
        if leave_request.status != LEAVE_STATUS_PENDING:
            raise LeaveInvalidStatusError

        balance = self._get_request_balance(leave_request)
        days = self._decimal(leave_request.requested_days)
        balance.pending_days = self._decimal(balance.pending_days) - days
        balance.used_days = self._decimal(balance.used_days) + days
        self._touch(balance, approver.user_id, request_ip)

        leave_request.status = LEAVE_STATUS_APPROVED
        leave_request.approved_at = self._now()
        self._touch(leave_request, approver.user_id, request_ip)
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def reject_request(
        self,
        *,
        leave_request_id: int,
        approver: User,
        payload: AdminLeaveRejectRequest,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """휴가 신청을 반려한다."""
        leave_request = self._get_request_or_raise(leave_request_id)
        self._ensure_assigned_approver(leave_request, approver.user_id)
        if leave_request.status != LEAVE_STATUS_PENDING:
            raise LeaveInvalidStatusError

        balance = self._get_request_balance(leave_request)
        days = self._decimal(leave_request.requested_days)
        balance.pending_days = self._decimal(balance.pending_days) - days
        balance.remaining_days = self._decimal(balance.remaining_days) + days
        self._touch(balance, approver.user_id, request_ip)

        leave_request.status = LEAVE_STATUS_REJECTED
        leave_request.rejected_at = self._now()
        leave_request.reject_reason = payload.reject_reason
        self._touch(leave_request, approver.user_id, request_ip)
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def cancel_request(
        self,
        *,
        leave_request_id: int,
        requester: User,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """신청자가 휴가 신청을 취소하거나 승인 후 취소를 요청한다."""
        leave_request = self._get_request_or_raise(leave_request_id)
        if leave_request.requester_id != requester.user_id:
            raise LeaveForbiddenError

        if leave_request.status in {LEAVE_STATUS_PENDING, LEAVE_STATUS_CHANGE_REQUESTED}:
            balance = self._get_request_balance(leave_request)
            days = self._decimal(leave_request.requested_days)
            balance.pending_days = self._decimal(balance.pending_days) - days
            balance.remaining_days = self._decimal(balance.remaining_days) + days
            self._touch(balance, requester.user_id, request_ip)
            leave_request.status = LEAVE_STATUS_CANCELED
            leave_request.canceled_at = self._now()
        elif leave_request.status == LEAVE_STATUS_APPROVED:
            leave_request.status = LEAVE_STATUS_CANCEL_REQUESTED
            leave_request.cancel_requested_at = self._now()
        else:
            raise LeaveInvalidStatusError

        self._touch(leave_request, requester.user_id, request_ip)
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def approve_cancel_request(
        self,
        *,
        leave_request_id: int,
        approver: User,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """승인 후 취소 요청을 승인한다."""
        leave_request = self._get_request_or_raise(leave_request_id)
        self._ensure_assigned_approver(leave_request, approver.user_id)
        if leave_request.status != LEAVE_STATUS_CANCEL_REQUESTED:
            raise LeaveInvalidStatusError

        balance = self._get_request_balance(leave_request)
        days = self._decimal(leave_request.requested_days)
        balance.used_days = self._decimal(balance.used_days) - days
        balance.remaining_days = self._decimal(balance.remaining_days) + days
        self._touch(balance, approver.user_id, request_ip)

        leave_request.status = LEAVE_STATUS_CANCELED
        leave_request.canceled_at = self._now()
        self._touch(leave_request, approver.user_id, request_ip)
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def request_change(
        self,
        *,
        leave_request_id: int,
        approver: User,
        payload: AdminLeaveChangeRequest,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """결재자가 승인/반려 대신 신청자에게 일정 변경을 요청한다.

        잔여일은 그대로 예약(pending)으로 유지하고 상태만 CHANGE_REQUESTED로
        바꾼다. 신청자는 이 요청을 보고 재신청(resubmit)하거나 취소할 수 있다.
        """
        leave_request = self._get_request_or_raise(leave_request_id)
        self._ensure_assigned_approver(leave_request, approver.user_id)
        if leave_request.status != LEAVE_STATUS_PENDING:
            raise LeaveInvalidStatusError

        leave_request.status = LEAVE_STATUS_CHANGE_REQUESTED
        leave_request.change_requested_at = self._now()
        leave_request.change_request_reason = payload.change_reason
        self._touch(leave_request, approver.user_id, request_ip)
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def resubmit_request(
        self,
        *,
        leave_request_id: int,
        requester: User,
        payload: AdminLeaveRequestCreate,
        request_ip: str | None,
    ) -> AdminLeaveRequestResponse:
        """신청자가 변경 요청을 반영해 일정을 수정하고 다시 결재를 올린다.

        기존 예약 일수를 원래 잔여에 되돌린 뒤 새 일수를 다시 예약하고,
        상태를 PENDING으로 되돌려 결재선을 재계산한다.
        """
        leave_request = self._get_request_or_raise(leave_request_id)
        if leave_request.requester_id != requester.user_id:
            raise LeaveForbiddenError
        if leave_request.status != LEAVE_STATUS_CHANGE_REQUESTED:
            raise LeaveInvalidStatusError

        new_days = self._calculate_requested_days(payload)
        approver = self._determine_approver(requester)
        if approver.user_id == requester.user_id:
            raise LeaveForbiddenError

        old_balance = self._get_request_balance(leave_request)
        old_days = self._decimal(leave_request.requested_days)
        new_balance = self._get_or_create_balance(
            user_id=requester.user_id,
            year=payload.start_date.year,
            actor_id=requester.user_id,
            request_ip=request_ip,
        )

        # 같은 잔여(같은 연도)면 기존 예약분을 되돌린 뒤의 가용량으로 판정한다.
        if new_balance.leave_balance_id == old_balance.leave_balance_id:
            available = self._decimal(new_balance.remaining_days) + old_days
        else:
            available = self._decimal(new_balance.remaining_days)
        if available < new_days:
            raise LeaveInsufficientBalanceError

        old_balance.pending_days = self._decimal(old_balance.pending_days) - old_days
        old_balance.remaining_days = self._decimal(old_balance.remaining_days) + old_days
        self._touch(old_balance, requester.user_id, request_ip)

        new_balance.pending_days = self._decimal(new_balance.pending_days) + new_days
        new_balance.remaining_days = self._decimal(new_balance.remaining_days) - new_days
        self._touch(new_balance, requester.user_id, request_ip)

        start_half_day, end_half_day = self._resolve_half_days(payload)

        leave_request.leave_type = payload.leave_type
        leave_request.start_date = payload.start_date
        leave_request.end_date = payload.end_date
        leave_request.start_half_day = start_half_day
        leave_request.end_half_day = end_half_day
        leave_request.requested_days = new_days
        leave_request.reason = payload.reason.strip() if payload.reason else None
        leave_request.leave_balance_id = new_balance.leave_balance_id
        leave_request.approver_id = approver.user_id
        leave_request.status = LEAVE_STATUS_PENDING
        leave_request.change_requested_at = None
        leave_request.change_request_reason = None
        self._touch(leave_request, requester.user_id, request_ip)
        self.db.commit()
        self.db.refresh(leave_request)
        return self._to_response(leave_request)

    def _resolve_half_days(self, payload: AdminLeaveRequestCreate) -> tuple[str | None, str | None]:
        """휴가 종류에 맞춰 시작/종료 반차 구분을 확정한다."""
        if payload.leave_type == LEAVE_TYPE_AM_HALF:
            return "AM", "AM"
        if payload.leave_type == LEAVE_TYPE_PM_HALF:
            return "PM", "PM"
        return payload.start_half_day, payload.end_half_day

    def _determine_approver(self, requester: User) -> User:
        if requester.admin_level == "A":
            approver = self.repository.find_super_admin(exclude_user_id=requester.user_id)
            if approver is None:
                raise LeaveApproverNotFoundError
            return approver

        if requester.team_role == TEAM_ROLE_LEAD:
            approver = self.repository.find_super_admin(exclude_user_id=requester.user_id)
            if approver is None:
                raise LeaveApproverNotFoundError
            return approver

        if requester.team_role == TEAM_ROLE_MEMBER and requester.team_id is not None:
            approver = self.repository.find_team_lead(
                team_id=requester.team_id,
                exclude_user_id=requester.user_id,
            )
            if approver is None:
                raise LeaveApproverNotFoundError
            return approver

        raise LeaveApproverNotFoundError

    def _calculate_requested_days(self, payload: AdminLeaveRequestCreate) -> Decimal:
        if payload.start_date.year != payload.end_date.year:
            raise LeaveInvalidRequestError

        if payload.leave_type in {LEAVE_TYPE_AM_HALF, LEAVE_TYPE_PM_HALF}:
            return HALF_DAY

        days = Decimal((payload.end_date - payload.start_date).days + 1)
        if payload.start_date == payload.end_date:
            if payload.start_half_day or payload.end_half_day:
                days = HALF_DAY
        else:
            if payload.start_half_day:
                days -= HALF_DAY
            if payload.end_half_day:
                days -= HALF_DAY

        if days <= 0:
            raise LeaveInvalidRequestError
        return days.quantize(DECIMAL_STEP)

    def _get_or_create_balance(
        self,
        *,
        user_id: int,
        year: int,
        actor_id: int,
        request_ip: str | None,
    ):
        balance = self.repository.get_balance_for_update(user_id=user_id, year=year)
        if balance is not None:
            return balance
        return self.repository.create_balance(
            user_id=user_id,
            year=year,
            granted_days=DEFAULT_GRANTED_DAYS,
            actor_id=actor_id,
            request_ip=request_ip,
        )

    def _get_request_or_raise(self, leave_request_id: int) -> AdminLeaveRequest:
        leave_request = self.repository.get_request_for_update(leave_request_id)
        if leave_request is None:
            raise LeaveRequestNotFoundError
        return leave_request

    def _get_request_balance(self, leave_request: AdminLeaveRequest):
        if leave_request.leave_balance_id is None:
            raise LeaveInvalidStatusError
        balance = self.repository.get_balance_by_id_for_update(leave_request.leave_balance_id)
        if balance is None:
            raise LeaveInvalidStatusError
        return balance

    def _ensure_assigned_approver(self, leave_request: AdminLeaveRequest, actor_id: int) -> None:
        if leave_request.requester_id == actor_id:
            raise LeaveForbiddenError
        if leave_request.approver_id != actor_id:
            raise LeaveForbiddenError

    def _to_response(self, leave_request: AdminLeaveRequest) -> AdminLeaveRequestResponse:
        return self._to_responses([leave_request])[0]

    def _to_responses(self, leave_requests: list[AdminLeaveRequest]) -> list[AdminLeaveRequestResponse]:
        user_ids: set[int] = set()
        for leave_request in leave_requests:
            user_ids.add(leave_request.requester_id)
            if leave_request.approver_id is not None:
                user_ids.add(leave_request.approver_id)
        users = self.repository.list_users_by_ids(user_ids)

        responses: list[AdminLeaveRequestResponse] = []
        for leave_request in leave_requests:
            requester = users.get(leave_request.requester_id)
            approver = users.get(leave_request.approver_id) if leave_request.approver_id else None
            responses.append(
                AdminLeaveRequestResponse(
                    leave_request_id=leave_request.leave_request_id,
                    requester_id=leave_request.requester_id,
                    requester_name=requester.name if requester else None,
                    requester_email=requester.email if requester else None,
                    approver_id=leave_request.approver_id,
                    approver_name=approver.name if approver else None,
                    approver_email=approver.email if approver else None,
                    leave_balance_id=leave_request.leave_balance_id,
                    leave_type=leave_request.leave_type,
                    start_date=leave_request.start_date,
                    end_date=leave_request.end_date,
                    start_half_day=leave_request.start_half_day,
                    end_half_day=leave_request.end_half_day,
                    requested_days=leave_request.requested_days,
                    reason=leave_request.reason,
                    status=leave_request.status,
                    approved_at=leave_request.approved_at,
                    rejected_at=leave_request.rejected_at,
                    reject_reason=leave_request.reject_reason,
                    canceled_at=leave_request.canceled_at,
                    cancel_requested_at=leave_request.cancel_requested_at,
                    change_requested_at=leave_request.change_requested_at,
                    change_request_reason=leave_request.change_request_reason,
                    created_at=leave_request.created_at,
                    updated_at=leave_request.updated_at,
                )
            )
        return responses

    @staticmethod
    def _decimal(value) -> Decimal:
        return Decimal(value).quantize(DECIMAL_STEP)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _touch(target, actor_id: int, request_ip: str | None) -> None:
        target.updated_by = actor_id
        target.updated_ip = request_ip
