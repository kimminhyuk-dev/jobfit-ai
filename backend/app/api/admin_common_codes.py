"""관리자 공통코드 관리 API."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user, require_permission
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.rbac import PERM_CODE_MANAGE
from app.models.user import User
from app.schemas.common_code import (
    CommonCodeGroupCreate,
    CommonCodeGroupResponse,
    CommonCodeGroupUpdate,
    CommonCodeItemCreate,
    CommonCodeItemResponse,
    CommonCodeItemUpdate,
)
from app.services.common_code_service import (
    CommonCodeDuplicateError,
    CommonCodeGroupHasItemsError,
    CommonCodeNotFoundError,
    CommonCodeService,
)

router = APIRouter(prefix="/admin/common-codes", tags=["admin-common-codes"])


def get_common_code_service(db: Session = Depends(get_db)) -> CommonCodeService:
    """CommonCodeService 의존성."""
    return CommonCodeService(db)


@router.get("/groups", response_model=list[CommonCodeGroupResponse])
def list_common_code_groups(
    _current_user: User = Depends(get_current_user),
    service: CommonCodeService = Depends(get_common_code_service),
) -> list[CommonCodeGroupResponse]:
    """공통코드 그룹 목록을 조회한다."""
    return service.list_groups()


@router.post("/groups", response_model=CommonCodeGroupResponse, status_code=status.HTTP_201_CREATED)
def create_common_code_group(
    payload: CommonCodeGroupCreate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_CODE_MANAGE)),
    service: CommonCodeService = Depends(get_common_code_service),
) -> CommonCodeGroupResponse:
    """공통코드 그룹을 생성한다."""
    try:
        return service.create_group(
            payload,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except CommonCodeDuplicateError as exc:
        raise _duplicate_code() from exc


@router.patch("/groups/{group_code}", response_model=CommonCodeGroupResponse)
def update_common_code_group(
    group_code: str,
    payload: CommonCodeGroupUpdate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_CODE_MANAGE)),
    service: CommonCodeService = Depends(get_common_code_service),
) -> CommonCodeGroupResponse:
    """공통코드 그룹을 수정한다."""
    try:
        return service.update_group(
            group_code,
            payload,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except CommonCodeNotFoundError as exc:
        raise _code_not_found() from exc
    except CommonCodeDuplicateError as exc:
        raise _duplicate_code() from exc


@router.delete("/groups/{group_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_common_code_group(
    group_code: str,
    request: Request,
    current_user: User = Depends(require_permission(PERM_CODE_MANAGE)),
    service: CommonCodeService = Depends(get_common_code_service),
) -> Response:
    """공통코드 그룹을 삭제한다."""
    try:
        service.delete_group(
            group_code,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except CommonCodeNotFoundError as exc:
        raise _code_not_found() from exc
    except CommonCodeGroupHasItemsError as exc:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.VALIDATION_ERROR,
            message="상세 코드가 있는 그룹은 삭제할 수 없습니다.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{group_code}/items", response_model=list[CommonCodeItemResponse])
def list_common_code_items(
    group_code: str,
    _current_user: User = Depends(get_current_user),
    service: CommonCodeService = Depends(get_common_code_service),
) -> list[CommonCodeItemResponse]:
    """그룹별 상세 코드 목록을 조회한다."""
    try:
        return service.list_items(group_code)
    except CommonCodeNotFoundError as exc:
        raise _code_not_found() from exc


@router.post(
    "/{group_code}/items",
    response_model=CommonCodeItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_common_code_item(
    group_code: str,
    payload: CommonCodeItemCreate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_CODE_MANAGE)),
    service: CommonCodeService = Depends(get_common_code_service),
) -> CommonCodeItemResponse:
    """상세 코드를 생성한다."""
    try:
        return service.create_item(
            group_code,
            payload,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except CommonCodeNotFoundError as exc:
        raise _code_not_found() from exc
    except CommonCodeDuplicateError as exc:
        raise _duplicate_code() from exc


@router.patch("/{group_code}/items/{code}", response_model=CommonCodeItemResponse)
def update_common_code_item(
    group_code: str,
    code: str,
    payload: CommonCodeItemUpdate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_CODE_MANAGE)),
    service: CommonCodeService = Depends(get_common_code_service),
) -> CommonCodeItemResponse:
    """상세 코드를 수정한다."""
    try:
        return service.update_item(
            group_code,
            code,
            payload,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except CommonCodeNotFoundError as exc:
        raise _code_not_found() from exc


@router.delete("/{group_code}/items/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_common_code_item(
    group_code: str,
    code: str,
    request: Request,
    current_user: User = Depends(require_permission(PERM_CODE_MANAGE)),
    service: CommonCodeService = Depends(get_common_code_service),
) -> Response:
    """상세 코드를 삭제한다."""
    try:
        service.delete_item(
            group_code,
            code,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except CommonCodeNotFoundError as exc:
        raise _code_not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _code_not_found() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.CODE_NOT_FOUND,
        message="공통코드를 찾을 수 없습니다.",
    )


def _duplicate_code() -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.VALIDATION_ERROR,
        message="이미 사용 중인 공통코드입니다.",
    )
