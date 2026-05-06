"""
관리자용 회원 관리 API 라우터
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_admin_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.resume import ResumeDetail, ResumeListItem, ResumeUpdate
from app.schemas.user import UserResponse
from app.services.resume_service import ResumeNotFoundError, ResumeService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    return ResumeService(db)


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    """관리자가 전체 회원 목록을 조회한다."""
    user_repo = UserRepository(db)
    users = user_repo.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=dict)
def get_user_detail(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    resume_service: ResumeService = Depends(get_resume_service),
) -> dict:
    """관리자가 특정 회원의 상세 정보와 이력서 목록을 조회한다."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.USER_NOT_FOUND,
            message="사용자를 찾을 수 없습니다.",
        )

    resumes = resume_service.list_resumes(user_id)
    return {
        "user": UserResponse.model_validate(user),
        "resumes": [ResumeListItem.model_validate(r) for r in resumes],
    }


@router.get("/resumes/{resume_id}", response_model=ResumeDetail)
def get_user_resume_detail(
    resume_id: int,
    current_admin: User = Depends(get_current_admin_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    """관리자가 특정 이력서의 상세 정보(파싱 데이터 포함)를 조회한다."""
    try:
        resume = resume_service.get_resume_for_admin(resume_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )
    return ResumeDetail.model_validate(resume)


@router.patch("/resumes/{resume_id}", response_model=ResumeDetail)
def update_user_resume_detail(
    resume_id: int,
    payload: ResumeUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    """관리자가 특정 이력서의 제목/추출 원문/파싱 결과를 수정한다."""
    parsed_data = (
        payload.parsed_data.model_dump(mode="json")
        if payload.parsed_data is not None
        else None
    )
    try:
        resume = resume_service.update_resume_content_for_admin(
            resume_id,
            actor_id=current_admin.user_id,
            title=payload.title,
            raw_text=payload.raw_text,
            parsed_data=parsed_data,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )
    return ResumeDetail.model_validate(resume)


@router.get("/resumes/{resume_id}/file")
def get_user_resume_file(
    resume_id: int,
    current_admin: User = Depends(get_current_admin_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> FileResponse:
    """관리자가 특정 이력서 파일을 스트리밍한다 (프리뷰용)."""
    try:
        resume = resume_service.get_resume_for_admin(resume_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )

    file_path = Path(resume.file_path)
    if not file_path.is_file():
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서 파일을 실제 저장소에서 찾을 수 없습니다.",
        )

    return FileResponse(
        path=resume.file_path,
        media_type=resume.content_type,
        filename=resume.original_filename,
    )
