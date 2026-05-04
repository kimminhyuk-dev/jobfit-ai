"""
이력서 API 라우터
"""

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.resume import ResumeDetail, ResumeListItem
from app.services.resume_service import (
    ResumeFileTooLargeError,
    ResumeNotFoundError,
    ResumeService,
    ResumeUnsupportedFileTypeError,
)


router = APIRouter(prefix="/resumes", tags=["resumes"])

UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    """ResumeService 의존성"""
    return ResumeService(db)


@router.get("", response_model=list[ResumeListItem])
def list_resumes(
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> list[ResumeListItem]:
    """현재 사용자의 이력서 목록을 조회한다."""
    resumes = resume_service.list_resumes(current_user.user_id)
    return [ResumeListItem.model_validate(resume) for resume in resumes]


@router.post("", response_model=ResumeDetail, status_code=status.HTTP_201_CREATED)
async def create_resume(
    request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    is_default: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    """이력서 파일을 업로드하고 텍스트 추출/기본 파싱을 수행한다."""
    content_type = file.content_type or "application/octet-stream"
    try:
        file_bytes = await _read_upload_file_limited(file)
    except ResumeFileTooLargeError:
        raise AppException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ErrorCode.RESUME_FILE_TOO_LARGE,
            message="이력서 파일은 최대 10MB까지 업로드할 수 있습니다.",
        )

    try:
        resume = resume_service.create_resume(
            user_id=current_user.user_id,
            original_filename=file.filename or "resume",
            content_type=content_type,
            file_bytes=file_bytes,
            title=title,
            is_default=is_default,
            request_ip=get_client_ip(request),
        )
    except ResumeFileTooLargeError:
        raise AppException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ErrorCode.RESUME_FILE_TOO_LARGE,
            message="이력서 파일은 최대 10MB까지 업로드할 수 있습니다.",
        )
    except ResumeUnsupportedFileTypeError:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.RESUME_UNSUPPORTED_FILE_TYPE,
            message="PDF, DOCX, TXT 파일만 업로드할 수 있습니다.",
        )

    return ResumeDetail.model_validate(resume)


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    """현재 사용자의 이력서 상세를 조회한다."""
    try:
        resume = resume_service.get_resume(resume_id, current_user.user_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )
    return ResumeDetail.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> Response:
    """현재 사용자의 이력서를 소프트 삭제한다."""
    try:
        resume_service.delete_resume(
            resume_id,
            user_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _read_upload_file_limited(file: UploadFile) -> bytes:
    """설정된 최대 용량을 넘기면 전체 파일을 메모리에 올리지 않고 중단한다."""
    max_bytes = settings.resume_max_upload_mb * 1024 * 1024
    chunks: list[bytes] = []
    total_size = 0

    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            raise ResumeFileTooLargeError
        chunks.append(chunk)

    return b"".join(chunks)
