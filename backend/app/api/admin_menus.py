"""관리자 동적 메뉴 API."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_client_ip,
    get_current_user,
    get_user_permission_codes,
    require_permission,
)
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.rbac import PERM_MENU_MANAGE
from app.models.user import User
from app.schemas.menu import MenuCreate, MenuResponse, MenuTreeResponse, MenuUpdate
from app.services.menu_service import (
    MenuInvalidParentError,
    MenuInvalidRequestError,
    MenuNotFoundError,
    MenuService,
)

router = APIRouter(prefix="/admin/menus", tags=["admin-menus"])


def get_menu_service(db: Session = Depends(get_db)) -> MenuService:
    """MenuService 의존성."""
    return MenuService(db)


@router.get("/tree", response_model=list[MenuTreeResponse])
def get_admin_menu_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: MenuService = Depends(get_menu_service),
) -> list[MenuTreeResponse]:
    """현재 사용자 권한 기준 관리자 메뉴 트리를 조회한다."""
    permission_codes = get_user_permission_codes(db, current_user)
    return service.get_tree_for_user(permission_codes)


@router.get("", response_model=list[MenuResponse])
def list_admin_menus(
    _current_user: User = Depends(require_permission(PERM_MENU_MANAGE)),
    service: MenuService = Depends(get_menu_service),
) -> list[MenuResponse]:
    """관리자 메뉴 전체 목록을 조회한다."""
    return service.list_menus()


@router.post("", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
def create_admin_menu(
    payload: MenuCreate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_MENU_MANAGE)),
    service: MenuService = Depends(get_menu_service),
) -> MenuResponse:
    """관리자 메뉴를 생성한다."""
    try:
        return service.create_menu(
            payload,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except MenuNotFoundError as exc:
        raise _menu_not_found() from exc
    except (MenuInvalidParentError, MenuInvalidRequestError) as exc:
        raise _invalid_menu_request() from exc


@router.patch("/{menu_id}", response_model=MenuResponse)
def update_admin_menu(
    menu_id: int,
    payload: MenuUpdate,
    request: Request,
    current_user: User = Depends(require_permission(PERM_MENU_MANAGE)),
    service: MenuService = Depends(get_menu_service),
) -> MenuResponse:
    """관리자 메뉴를 수정한다."""
    try:
        return service.update_menu(
            menu_id,
            payload,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except MenuNotFoundError as exc:
        raise _menu_not_found() from exc
    except (MenuInvalidParentError, MenuInvalidRequestError) as exc:
        raise _invalid_menu_request() from exc


@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_menu(
    menu_id: int,
    request: Request,
    current_user: User = Depends(require_permission(PERM_MENU_MANAGE)),
    service: MenuService = Depends(get_menu_service),
) -> Response:
    """관리자 메뉴를 삭제한다."""
    try:
        service.delete_menu(
            menu_id,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except MenuNotFoundError as exc:
        raise _menu_not_found() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _menu_not_found() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.NOT_FOUND,
        message="메뉴를 찾을 수 없습니다.",
    )


def _invalid_menu_request() -> AppException:
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.VALIDATION_ERROR,
        message="메뉴 설정이 올바르지 않습니다.",
    )
