"""Resume API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.resume import ResumeDetail, ResumeListItem
from app.schemas.resume_interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewSessionCreateResponse,
    InterviewSessionDetailResponse,
)
from app.services.rag.embedding import (
    EmbeddingGenerationError,
    EmbeddingNotConfiguredError,
)
from app.services.rag.resume_chunk_service import (
    ResumeChunkRebuildError,
    rebuild_resume_chunks,
)
from app.services.interview_practice_service import (
    InterviewPracticeEvaluationError,
    InterviewPracticeGenerationError,
    InterviewPracticeInvalidResumeError,
    InterviewPracticeProviderNotConfiguredError,
    InterviewPracticeQuestionNotFoundError,
    InterviewPracticeService,
    InterviewPracticeSessionNotFoundError,
)
from app.services.resume_service import (
    ResumeFileTooLargeError,
    ResumeNotFoundError,
    ResumeService,
    ResumeUnsupportedFileTypeError,
)


router = APIRouter(prefix="/resumes", tags=["resumes"])

UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    """ResumeService dependency."""
    return ResumeService(db)


def get_interview_practice_service(
    db: Session = Depends(get_db),
) -> InterviewPracticeService:
    """InterviewPracticeService dependency."""
    return InterviewPracticeService(db)


@router.get("", response_model=list[ResumeListItem])
def list_resumes(
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> list[ResumeListItem]:
    """List resumes owned by the current user."""
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
    """Upload a resume file and parse its content."""
    content_type = file.content_type or "application/octet-stream"
    try:
        file_bytes = await _read_upload_file_limited(file)
    except ResumeFileTooLargeError:
        raise AppException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code=ErrorCode.RESUME_FILE_TOO_LARGE,
            message="Resume files can be up to 10MB.",
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
            message="Resume files can be up to 10MB.",
        )
    except ResumeUnsupportedFileTypeError:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.RESUME_UNSUPPORTED_FILE_TYPE,
            message="등록 가능한 파일 형식 및 확장자 : PDF,PNG,JPG,JPEG,GIF",
        )

    return ResumeDetail.model_validate(resume)


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    """Return a resume owned by the current user."""
    try:
        resume = resume_service.get_resume(resume_id, current_user.user_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )
    return ResumeDetail.model_validate(resume)


@router.post("/{resume_id}/chunks/rebuild")
def rebuild_resume_chunks_endpoint(
    resume_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
    db: Session = Depends(get_db),
) -> dict:
    """이력서 섹션 청크와 임베딩을 재생성한다."""

    try:
        if current_user.role == "ADMIN":
            resume_service.get_resume_for_admin(resume_id)
        else:
            resume_service.get_resume(resume_id, current_user.user_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )

    try:
        return rebuild_resume_chunks(
            db,
            resume_id,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )
    except EmbeddingNotConfiguredError:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.OPENAI_API_KEY_MISSING,
            message="OpenAI API configuration is required.",
        )
    except (EmbeddingGenerationError, ResumeChunkRebuildError):
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.RESUME_CHUNK_EMBEDDING_FAILED,
            message="Failed to rebuild resume chunks. Please try again later.",
        )


@router.post(
    "/{resume_id}/interview-sessions",
    response_model=InterviewSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resume_interview_session(
    resume_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(
        get_interview_practice_service
    ),
) -> InterviewSessionCreateResponse:
    """Create an interview practice session and persist 5 questions."""
    try:
        return interview_practice_service.create_session(
            resume_id=resume_id,
            user_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )
    except InterviewPracticeInvalidResumeError:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.RESUME_NOT_PARSED,
            message="Resume parsing must be completed before interview practice.",
        )
    except InterviewPracticeProviderNotConfiguredError:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.OPENAI_API_KEY_MISSING,
            message="OpenAI API configuration is required.",
        )
    except InterviewPracticeGenerationError:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.INTERVIEW_QUESTION_GENERATION_FAILED,
            message="Failed to generate interview questions. Please try again later.",
        )


@router.get(
    "/{resume_id}/interview-sessions/{session_id}",
    response_model=InterviewSessionDetailResponse,
)
def get_resume_interview_session(
    resume_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(
        get_interview_practice_service
    ),
) -> InterviewSessionDetailResponse:
    """Return a persisted interview session without calling OpenAI."""
    try:
        return interview_practice_service.get_session(
            resume_id=resume_id,
            session_id=session_id,
            user_id=current_user.user_id,
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )
    except InterviewPracticeSessionNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.INTERVIEW_SESSION_NOT_FOUND,
            message="Interview practice session not found.",
        )


@router.post(
    "/{resume_id}/interview-questions/{question_id}/answer",
    response_model=InterviewAnswerResponse,
)
def submit_resume_interview_answer(
    resume_id: int,
    question_id: int,
    payload: InterviewAnswerRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    interview_practice_service: InterviewPracticeService = Depends(
        get_interview_practice_service
    ),
) -> InterviewAnswerResponse:
    """Evaluate and persist one answer for an interview practice question."""
    try:
        return interview_practice_service.submit_answer(
            resume_id=resume_id,
            question_id=question_id,
            user_id=current_user.user_id,
            answer=payload.answer,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )
    except InterviewPracticeQuestionNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.INTERVIEW_QUESTION_NOT_FOUND,
            message="Interview question not found.",
        )
    except InterviewPracticeProviderNotConfiguredError:
        raise AppException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.OPENAI_API_KEY_MISSING,
            message="OpenAI API configuration is required.",
        )
    except InterviewPracticeEvaluationError:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.INTERVIEW_ANSWER_EVALUATION_FAILED,
            message="Failed to evaluate interview answer. Please try again later.",
        )


@router.get("/{resume_id}/file")
def get_resume_file(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> FileResponse:
    """Stream the original resume file for preview."""
    try:
        resume = resume_service.get_resume(resume_id, current_user.user_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume not found.",
        )

    file_path = Path(resume.file_path)
    if not file_path.is_file():
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="Resume file not found in storage.",
        )

    return FileResponse(
        path=resume.file_path,
        media_type=resume.content_type,
        filename=resume.original_filename,
        content_disposition_type="inline",
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> Response:
    """Soft-delete a resume owned by the current user."""
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
            message="Resume not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _read_upload_file_limited(file: UploadFile) -> bytes:
    """Read an upload while enforcing the configured max file size."""
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
