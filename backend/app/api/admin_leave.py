"""관리자 휴가 신청/결재 API routes."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, require_permission
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.rbac import PERM_LEAVE_APPROVE, PERM_LEAVE_REQUEST
from app.models.user import User
from app.schemas.admin_leave import (
    AdminLeaveChangeRequest,
    AdminLeaveRejectRequest,
    AdminLeaveRequestCreate,
    AdminLeaveRequestResponse,
)
from app.services.admin_leave_service import (
    AdminLeaveService,
    LeaveApproverNotFoundError,
    LeaveForbiddenError,
    LeaveInsufficientBalanceError,
    LeaveInvalidRequestError,
    LeaveInvalidStatusError,
    LeaveRequestNotFoundError,
)

router = APIRouter(prefix="/admin/leave", tags=["admin-leave"])


def get_admin_leave_service(db: Session = Depends(get_db)) -> AdminLeaveService:
    """AdminLeaveService dependency."""
    return AdminLeaveService(db)


@router.post("", response_model=AdminLeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    payload: AdminLeaveRequestCreate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_REQUEST)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """휴가를 신청한다."""
    try:
        return leave_service.create_request(
            requester=current_user,
            payload=payload,
            request_ip=get_client_ip(request),
        )
    except LeaveInvalidRequestError as exc:
        raise _invalid_request() from exc
    except LeaveApproverNotFoundError as exc:
        raise _approver_not_found() from exc
    except LeaveInsufficientBalanceError as exc:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.LEAVE_INSUFFICIENT_BALANCE,
            message="휴가 잔여일이 부족합니다.",
        ) from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc


@router.get("/me", response_model=list[AdminLeaveRequestResponse])
def list_my_leave_requests(
    current_user: User = Depends(require_permission(PERM_LEAVE_REQUEST)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> list[AdminLeaveRequestResponse]:
    """내 휴가 신청 목록을 조회한다."""
    return leave_service.list_my_requests(current_user.user_id)


@router.get("/pending", response_model=list[AdminLeaveRequestResponse])
def list_pending_leave_approvals(
    current_user: User = Depends(require_permission(PERM_LEAVE_APPROVE)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> list[AdminLeaveRequestResponse]:
    """내가 결재해야 할 휴가 신청 목록을 조회한다."""
    return leave_service.list_pending_approvals(current_user.user_id)


@router.patch("/{leave_request_id}/approve", response_model=AdminLeaveRequestResponse)
def approve_leave_request(
    leave_request_id: int,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_APPROVE)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """휴가 신청을 승인한다."""
    try:
        return leave_service.approve_request(
            leave_request_id=leave_request_id,
            approver=current_user,
            request_ip=get_client_ip(request),
        )
    except LeaveRequestNotFoundError as exc:
        raise _leave_not_found() from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc
    except LeaveInvalidStatusError as exc:
        raise _invalid_status() from exc


@router.patch("/{leave_request_id}/reject", response_model=AdminLeaveRequestResponse)
def reject_leave_request(
    leave_request_id: int,
    payload: AdminLeaveRejectRequest,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_APPROVE)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """휴가 신청을 반려한다."""
    try:
        return leave_service.reject_request(
            leave_request_id=leave_request_id,
            approver=current_user,
            payload=payload,
            request_ip=get_client_ip(request),
        )
    except LeaveRequestNotFoundError as exc:
        raise _leave_not_found() from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc
    except LeaveInvalidStatusError as exc:
        raise _invalid_status() from exc


@router.patch("/{leave_request_id}/cancel", response_model=AdminLeaveRequestResponse)
def cancel_leave_request(
    leave_request_id: int,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_REQUEST)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """휴가 신청을 취소하거나 승인 후 취소를 요청한다."""
    try:
        return leave_service.cancel_request(
            leave_request_id=leave_request_id,
            requester=current_user,
            request_ip=get_client_ip(request),
        )
    except LeaveRequestNotFoundError as exc:
        raise _leave_not_found() from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc
    except LeaveInvalidStatusError as exc:
        raise _invalid_status() from exc


@router.patch("/{leave_request_id}/cancel-approve", response_model=AdminLeaveRequestResponse)
def approve_leave_cancel_request(
    leave_request_id: int,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_APPROVE)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """승인 후 취소 요청을 승인한다."""
    try:
        return leave_service.approve_cancel_request(
            leave_request_id=leave_request_id,
            approver=current_user,
            request_ip=get_client_ip(request),
        )
    except LeaveRequestNotFoundError as exc:
        raise _leave_not_found() from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc
    except LeaveInvalidStatusError as exc:
        raise _invalid_status() from exc


@router.patch("/{leave_request_id}/request-change", response_model=AdminLeaveRequestResponse)
def request_leave_change(
    leave_request_id: int,
    payload: AdminLeaveChangeRequest,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_APPROVE)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """결재자가 신청자에게 일정 변경을 요청한다."""
    try:
        return leave_service.request_change(
            leave_request_id=leave_request_id,
            approver=current_user,
            payload=payload,
            request_ip=get_client_ip(request),
        )
    except LeaveRequestNotFoundError as exc:
        raise _leave_not_found() from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc
    except LeaveInvalidStatusError as exc:
        raise _invalid_status() from exc


@router.patch("/{leave_request_id}/resubmit", response_model=AdminLeaveRequestResponse)
def resubmit_leave_request(
    leave_request_id: int,
    payload: AdminLeaveRequestCreate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_LEAVE_REQUEST)),
    leave_service: AdminLeaveService = Depends(get_admin_leave_service),
) -> AdminLeaveRequestResponse:
    """신청자가 변경 요청을 반영해 일정을 수정하고 다시 결재를 올린다."""
    try:
        return leave_service.resubmit_request(
            leave_request_id=leave_request_id,
            requester=current_user,
            payload=payload,
            request_ip=get_client_ip(request),
        )
    except LeaveRequestNotFoundError as exc:
        raise _leave_not_found() from exc
    except LeaveInvalidRequestError as exc:
        raise _invalid_request() from exc
    except LeaveApproverNotFoundError as exc:
        raise _approver_not_found() from exc
    except LeaveInsufficientBalanceError as exc:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.LEAVE_INSUFFICIENT_BALANCE,
            message="휴가 잔여일이 부족합니다.",
        ) from exc
    except LeaveForbiddenError as exc:
        raise _leave_forbidden() from exc
    except LeaveInvalidStatusError as exc:
        raise _invalid_status() from exc


def _leave_not_found() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.LEAVE_REQUEST_NOT_FOUND,
        message="휴가 신청을 찾을 수 없습니다.",
    )


def _leave_forbidden() -> AppException:
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ErrorCode.FORBIDDEN,
        message="해당 휴가 신청을 처리할 권한이 없습니다.",
    )


def _invalid_status() -> AppException:
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.LEAVE_INVALID_STATUS,
        message="현재 상태에서는 처리할 수 없습니다.",
    )


def _approver_not_found() -> AppException:
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.LEAVE_APPROVER_NOT_FOUND,
        message="휴가 결재선을 찾을 수 없습니다.",
    )


def _invalid_request() -> AppException:
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.LEAVE_INVALID_REQUEST,
        message="휴가 신청 내용이 올바르지 않습니다.",
    )
