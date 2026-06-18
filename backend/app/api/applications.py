"""Application(지원/이력서 보내기) API routes."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    MyApplicationItem,
)
from app.services.application_service import (
    ApplicationAlreadyExistsError,
    ApplicationJobNotFoundError,
    ApplicationNotFoundError,
    ApplicationResumeNotFoundError,
    ApplicationService,
)

router = APIRouter(prefix="/applications", tags=["applications"])


def get_application_service(db: Session = Depends(get_db)) -> ApplicationService:
    """ApplicationService dependency."""
    return ApplicationService(db)


def _require_user(current_user: User) -> None:
    """지원 생성은 개인회원(USER)만 허용한다."""
    if (current_user.role or "").strip().upper() != "USER":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="개인회원만 지원할 수 있습니다.",
        )


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """선택한 이력서로 공고에 지원한다(이력서 보내기)."""
    _require_user(current_user)
    try:
        return application_service.apply(
            user_id=current_user.user_id,
            job_id=payload.job_id,
            resume_id=payload.resume_id,
            request_ip=get_client_ip(request),
        )
    except ApplicationResumeNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        ) from exc
    except ApplicationJobNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.JOB_NOT_FOUND,
            message="공고를 찾을 수 없습니다.",
        ) from exc
    except ApplicationAlreadyExistsError as exc:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.APPLICATION_ALREADY_EXISTS,
            message="이미 지원한 공고입니다.",
        ) from exc


@router.get("/me", response_model=list[MyApplicationItem])
def list_my_applications(
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
) -> list[MyApplicationItem]:
    """내 지원현황을 최신순으로 조회한다."""
    return application_service.list_my_applications(current_user.user_id)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_application(
    application_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    application_service: ApplicationService = Depends(get_application_service),
) -> Response:
    """내 지원을 취소한다(취소 후 같은 공고에 재지원 가능)."""
    try:
        application_service.cancel_application(
            application_id=application_id,
            user_id=current_user.user_id,
            request_ip=get_client_ip(request),
        )
    except ApplicationNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.APPLICATION_NOT_FOUND,
            message="취소할 지원 내역을 찾을 수 없습니다.",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
