"""기업회원(Company) API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.company import (
    CompanyApplicationStatusResponse,
    CompanyApplicationStatusUpdateRequest,
    CompanyApplicantResumeResponse,
    CompanyDashboardResponse,
    CompanyJobCreateRequest,
    CompanyJobItem,
    CompanyJobUpdateRequest,
    InterviewEmailRequest,
    InterviewEmailResponse,
)
from app.services.company_service import (
    CompanyAccountNotFoundError,
    CompanyApplicationInvalidStatusError,
    CompanyApplicationNotFoundError,
    CompanyJobNotEditableError,
    CompanyJobNotFoundError,
    CompanyService,
    InterviewEmailSendError,
    InterviewLocationMissingError,
)

router = APIRouter(prefix="/company", tags=["company"])


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    """CompanyService dependency."""
    return CompanyService(db)


def _require_company(current_user: User) -> None:
    if (current_user.role or "").strip().upper() != "COMPANY":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="기업회원만 접근할 수 있습니다.",
        )


@router.get("/dashboard", response_model=CompanyDashboardResponse)
def get_company_dashboard(
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyDashboardResponse:
    """기업회원의 대시보드(받은 지원자 현황 + 통계)를 조회한다."""
    _require_company(current_user)
    try:
        return company_service.get_dashboard(current_user.user_id)
    except CompanyAccountNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.COMPANY_NOT_FOUND,
            message="기업 계정 정보를 찾을 수 없습니다.",
        ) from exc


@router.get(
    "/applications/{application_id}/resume",
    response_model=CompanyApplicantResumeResponse,
)
def view_applicant_resume(
    application_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyApplicantResumeResponse:
    """지원자 이력서를 열람한다(첫 열람 시 상태가 '이력서 열람'으로 바뀐다)."""
    _require_company(current_user)
    try:
        return company_service.view_applicant_resume(
            user_id=current_user.user_id,
            application_id=application_id,
            request_ip=get_client_ip(request),
        )
    except CompanyAccountNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.COMPANY_NOT_FOUND,
            message="기업 계정 정보를 찾을 수 없습니다.",
        ) from exc
    except CompanyApplicationNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.APPLICATION_NOT_FOUND,
            message="해당 지원 내역을 찾을 수 없습니다.",
        ) from exc


@router.get("/applications/{application_id}/resume/file")
def get_applicant_resume_file(
    application_id: int,
    download: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> FileResponse:
    """지원서에 첨부된 원본 이력서 파일을 미리보기 또는 다운로드로 반환한다."""
    _require_company(current_user)
    try:
        resume = company_service.get_applicant_resume_file(
            user_id=current_user.user_id,
            application_id=application_id,
        )
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyApplicationNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.APPLICATION_NOT_FOUND,
            message="해당 지원 내역을 찾을 수 없습니다.",
        ) from exc

    file_path = Path(resume.file_path)
    if not file_path.is_file():
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서 파일을 저장소에서 찾을 수 없습니다.",
        )

    return FileResponse(
        path=resume.file_path,
        media_type=resume.content_type,
        filename=resume.original_filename,
        content_disposition_type="attachment" if download else "inline",
    )


@router.post(
    "/applications/{application_id}/interview-email",
    response_model=InterviewEmailResponse,
)
def send_interview_email(
    application_id: int,
    payload: InterviewEmailRequest,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> InterviewEmailResponse:
    """지원자에게 면접 안내 메일(면접 장소 지도 포함)을 발송한다."""
    _require_company(current_user)
    try:
        return company_service.send_interview_email(
            user_id=current_user.user_id,
            application_id=application_id,
            payload=payload,
        )
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyApplicationNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.APPLICATION_NOT_FOUND,
            message="해당 지원 내역을 찾을 수 없습니다.",
        ) from exc
    except InterviewLocationMissingError as exc:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.INTERVIEW_EMAIL_FAILED,
            message="면접 장소 주소가 없습니다. 기업 주소를 등록하거나 요청에 주소를 포함해 주세요.",
        ) from exc
    except InterviewEmailSendError as exc:
        raise AppException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=ErrorCode.INTERVIEW_EMAIL_FAILED,
            message="면접 안내 메일 발송에 실패했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc


@router.patch(
    "/applications/{application_id}/status",
    response_model=CompanyApplicationStatusResponse,
)
def update_application_status(
    application_id: int,
    payload: CompanyApplicationStatusUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyApplicationStatusResponse:
    """기업이 받은 지원을 탈락 처리한다."""
    _require_company(current_user)
    try:
        return company_service.update_application_status(
            user_id=current_user.user_id,
            application_id=application_id,
            status=payload.status,
            request_ip=get_client_ip(request),
        )
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyApplicationNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.APPLICATION_NOT_FOUND,
            message="해당 지원 내역을 찾을 수 없습니다.",
        ) from exc
    except CompanyApplicationInvalidStatusError as exc:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.APPLICATION_INVALID_STATUS,
            message="변경할 수 없는 지원 상태입니다.",
        ) from exc


@router.get("/jobs", response_model=list[CompanyJobItem])
def list_company_jobs(
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> list[CompanyJobItem]:
    """기업이 등록/연결된 공고 목록을 조회한다."""
    _require_company(current_user)
    try:
        return company_service.list_company_jobs(current_user.user_id)
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc


@router.post(
    "/jobs",
    response_model=CompanyJobItem,
    status_code=status.HTTP_201_CREATED,
)
def create_company_job(
    payload: CompanyJobCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyJobItem:
    """기업이 새 공고를 등록한다."""
    _require_company(current_user)
    try:
        return company_service.create_company_job(
            user_id=current_user.user_id,
            payload=payload,
            request_ip=get_client_ip(request),
        )
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc


@router.get("/jobs/{job_id}", response_model=CompanyJobItem)
def get_company_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyJobItem:
    """기업 공고 상세를 조회한다."""
    _require_company(current_user)
    try:
        return company_service.get_company_job(current_user.user_id, job_id)
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyJobNotFoundError as exc:
        raise _job_not_found() from exc


@router.patch("/jobs/{job_id}", response_model=CompanyJobItem)
def update_company_job(
    job_id: int,
    payload: CompanyJobUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyJobItem:
    """기업이 등록한 공고를 수정한다(외부 수집 공고는 수정 불가)."""
    _require_company(current_user)
    try:
        return company_service.update_company_job(
            user_id=current_user.user_id,
            job_id=job_id,
            payload=payload,
            request_ip=get_client_ip(request),
        )
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyJobNotFoundError as exc:
        raise _job_not_found() from exc
    except CompanyJobNotEditableError as exc:
        raise _job_not_editable() from exc


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_job(
    job_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> Response:
    """기업이 등록한 공고를 삭제한다(외부 수집 공고는 삭제 불가)."""
    _require_company(current_user)
    try:
        company_service.delete_company_job(
            user_id=current_user.user_id,
            job_id=job_id,
            request_ip=get_client_ip(request),
        )
    except CompanyAccountNotFoundError as exc:
        raise _company_not_found() from exc
    except CompanyJobNotFoundError as exc:
        raise _job_not_found() from exc
    except CompanyJobNotEditableError as exc:
        raise _job_not_editable() from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _company_not_found() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.COMPANY_NOT_FOUND,
        message="기업 계정 정보를 찾을 수 없습니다.",
    )


def _job_not_found() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.JOB_NOT_FOUND,
        message="해당 공고를 찾을 수 없습니다.",
    )


def _job_not_editable() -> AppException:
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ErrorCode.JOB_NOT_EDITABLE,
        message="외부 수집 공고는 수정하거나 삭제할 수 없습니다.",
    )
