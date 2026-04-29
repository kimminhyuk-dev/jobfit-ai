"""
게시글 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse, PostUpdate
from app.services.post_service import (
    PostCategoryNotFoundError,
    PostNotFoundError,
    PostService,
)


router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    """PostService 의존성"""
    return PostService(db)


@router.get("", response_model=list[PostResponse])
def list_posts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    category_id: int | None = Query(default=None, gt=0),
    post_service: PostService = Depends(get_post_service),
) -> list[PostResponse]:
    """게시글 목록을 조회한다."""
    posts = post_service.list_posts(
        offset=offset,
        limit=limit,
        category_id=category_id,
    )
    return [PostResponse.model_validate(post) for post in posts]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_create: PostCreate,
    current_user: User = Depends(get_current_admin_user),
    post_service: PostService = Depends(get_post_service),
) -> PostResponse:
    """관리자가 Q&A 게시글을 생성한다."""
    try:
        post = post_service.create_post(post_create, author_id=current_user.user_id)
    except PostCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="활성 카테고리를 찾을 수 없습니다.",
        )
    return PostResponse.model_validate(post)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    post_service: PostService = Depends(get_post_service),
) -> PostResponse:
    """게시글 상세를 조회한다."""
    try:
        post = post_service.get_post(post_id)
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )
    return PostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_admin_user),
    post_service: PostService = Depends(get_post_service),
) -> PostResponse:
    """관리자가 Q&A 게시글을 수정한다."""
    try:
        post = post_service.update_post(
            post_id,
            post_update,
            updater_id=current_user.user_id,
        )
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )
    except PostCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="활성 카테고리를 찾을 수 없습니다.",
        )
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_admin_user),
    post_service: PostService = Depends(get_post_service),
) -> Response:
    """관리자가 Q&A 게시글을 삭제한다."""
    try:
        post_service.delete_post(post_id, deleter_id=current_user.user_id)
    except PostNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
