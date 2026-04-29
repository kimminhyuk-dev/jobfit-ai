"""
카테고리 API 라우터
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import (
    CategoryNotFoundError,
    CategoryService,
    DuplicateCategorySlugError,
)


router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """CategoryService 의존성"""
    return CategoryService(db)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    category_service: CategoryService = Depends(get_category_service),
) -> list[CategoryResponse]:
    """활성 카테고리 목록을 조회한다."""
    categories = category_service.list_categories()
    return [CategoryResponse.model_validate(category) for category in categories]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_create: CategoryCreate,
    current_user: User = Depends(get_current_admin_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """관리자가 카테고리를 생성한다."""
    try:
        category = category_service.create_category(
            category_create,
            actor_id=current_user.user_id,
        )
    except DuplicateCategorySlugError:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.DUPLICATE_CATEGORY_SLUG,
            message="이미 사용 중인 카테고리 slug입니다.",
        )
    return CategoryResponse.model_validate(category)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """활성 카테고리 상세를 조회한다."""
    try:
        category = category_service.get_category(category_id)
    except CategoryNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.CATEGORY_NOT_FOUND,
            message="카테고리를 찾을 수 없습니다.",
        )
    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_admin_user),
    category_service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    """관리자가 카테고리를 수정한다."""
    try:
        category = category_service.update_category(
            category_id,
            category_update,
            actor_id=current_user.user_id,
        )
    except CategoryNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.CATEGORY_NOT_FOUND,
            message="카테고리를 찾을 수 없습니다.",
        )
    except DuplicateCategorySlugError:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.DUPLICATE_CATEGORY_SLUG,
            message="이미 사용 중인 카테고리 slug입니다.",
        )
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_admin_user),
    category_service: CategoryService = Depends(get_category_service),
) -> Response:
    """관리자가 카테고리를 소프트 삭제한다."""
    try:
        category_service.delete_category(category_id, actor_id=current_user.user_id)
    except CategoryNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.CATEGORY_NOT_FOUND,
            message="카테고리를 찾을 수 없습니다.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
