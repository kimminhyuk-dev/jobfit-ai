"""채팅형 모의면접 API."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.mock_interview import (
    MockInterviewAnswerRequest,
    MockInterviewAnswerResponse,
    MockInterviewFinishResponse,
    MockInterviewSessionResponse,
    MockInterviewStartRequest,
    MockInterviewStartResponse,
)
from app.services.mock_interview_service import (
    MockInterviewGenerationError,
    MockInterviewInvalidResumeError,
    MockInterviewInvalidStateError,
    MockInterviewJobNotFoundError,
    MockInterviewNoJobError,
    MockInterviewProviderNotConfiguredError,
    MockInterviewService,
    MockInterviewSessionNotFoundError,
)
from app.services.resume_service import ResumeNotFoundError


router = APIRouter(prefix="/mock-interview", tags=["mock-interview"])


def get_mock_interview_service(
    db: Session = Depends(get_db),
) -> MockInterviewService:
    """모의면접 서비스 의존성."""

    return MockInterviewService(db)


@router.post(
    "/start",
    response_model=MockInterviewStartResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_mock_interview(
    payload: MockInterviewStartRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    mock_interview_service: MockInterviewService = Depends(
        get_mock_interview_service
    ),
) -> MockInterviewStartResponse:
    """모의면접 세션을 시작하고 첫 질문을 만든다."""

    try:
        return mock_interview_service.start(
            resume_id=payload.resume_id,
            user_id=current_user.user_id,
            job_id=payload.job_id,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise _not_found(ErrorCode.RESUME_NOT_FOUND, "Resume not found.")
    except MockInterviewInvalidResumeError:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.RESUME_NOT_PARSED,
            message="Resume parsing must be completed first.",
        )
    except MockInterviewNoJobError:
        raise _not_found(
            ErrorCode.APPLICATION_NOT_FOUND,
            "No applied job was found for this resume.",
        )
    except MockInterviewJobNotFoundError:
        raise _not_found(ErrorCode.JOB_NOT_FOUND, "Job posting not found.")
    except MockInterviewProviderNotConfiguredError:
        raise _openai_missing()
    except MockInterviewGenerationError:
        raise _generation_failed()


@router.post(
    "/{session_id}/answer",
    response_model=MockInterviewAnswerResponse,
)
def answer_mock_interview(
    session_id: int,
    payload: MockInterviewAnswerRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    mock_interview_service: MockInterviewService = Depends(
        get_mock_interview_service
    ),
) -> MockInterviewAnswerResponse:
    """현재 질문에 답변하고 다음 질문을 만든다."""

    try:
        return mock_interview_service.answer(
            session_id=session_id,
            user_id=current_user.user_id,
            answer=payload.answer.strip(),
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except MockInterviewSessionNotFoundError:
        raise _not_found(
            ErrorCode.INTERVIEW_SESSION_NOT_FOUND,
            "Mock interview session not found.",
        )
    except ResumeNotFoundError:
        raise _not_found(ErrorCode.RESUME_NOT_FOUND, "Resume not found.")
    except MockInterviewInvalidStateError:
        raise _invalid_state()
    except MockInterviewInvalidResumeError:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.RESUME_NOT_PARSED,
            message="Resume parsing must be completed first.",
        )
    except MockInterviewJobNotFoundError:
        raise _not_found(ErrorCode.JOB_NOT_FOUND, "Job posting not found.")
    except MockInterviewProviderNotConfiguredError:
        raise _openai_missing()
    except MockInterviewGenerationError:
        raise _generation_failed()


@router.post(
    "/{session_id}/finish",
    response_model=MockInterviewFinishResponse,
)
def finish_mock_interview(
    session_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    mock_interview_service: MockInterviewService = Depends(
        get_mock_interview_service
    ),
) -> MockInterviewFinishResponse:
    """모의면접을 종료하고 종합 리포트를 만든다."""

    try:
        return mock_interview_service.finish(
            session_id=session_id,
            user_id=current_user.user_id,
            actor_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except MockInterviewSessionNotFoundError:
        raise _not_found(
            ErrorCode.INTERVIEW_SESSION_NOT_FOUND,
            "Mock interview session not found.",
        )
    except MockInterviewInvalidStateError:
        raise _invalid_state()
    except MockInterviewJobNotFoundError:
        raise _not_found(ErrorCode.JOB_NOT_FOUND, "Job posting not found.")
    except MockInterviewProviderNotConfiguredError:
        raise _openai_missing()
    except MockInterviewGenerationError:
        raise _generation_failed()


@router.get("/{session_id}", response_model=MockInterviewSessionResponse)
def get_mock_interview(
    session_id: int,
    current_user: User = Depends(get_current_user),
    mock_interview_service: MockInterviewService = Depends(
        get_mock_interview_service
    ),
) -> MockInterviewSessionResponse:
    """모의면접 세션과 대화 전체를 조회한다."""

    try:
        return mock_interview_service.get_session(
            session_id=session_id,
            user_id=current_user.user_id,
        )
    except MockInterviewSessionNotFoundError:
        raise _not_found(
            ErrorCode.INTERVIEW_SESSION_NOT_FOUND,
            "Mock interview session not found.",
        )


def _not_found(code: ErrorCode, message: str) -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=code,
        message=message,
    )


def _invalid_state() -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.INTERVIEW_ANSWER_EVALUATION_FAILED,
        message="Mock interview state is not valid for this action.",
    )


def _openai_missing() -> AppException:
    return AppException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code=ErrorCode.OPENAI_API_KEY_MISSING,
        message="OpenAI API configuration is required.",
    )


def _generation_failed() -> AppException:
    return AppException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        code=ErrorCode.INTERVIEW_QUESTION_GENERATION_FAILED,
        message="Failed to continue mock interview. Please try again later.",
    )
