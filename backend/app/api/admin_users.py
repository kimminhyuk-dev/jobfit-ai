"""Admin user management routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_admin_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_user import AdminCompanySummary, AdminUserDetail, AdminUserListItem
from app.schemas.resume import (
    ResumeCoverLetterSectionResponse,
    ResumeDetail,
    ResumeListItem,
    ResumeProjectResponse,
    ResumeUpdate,
)
from app.services.resume_service import ResumeNotFoundError, ResumeService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_resume_service(db: Session = Depends(get_db)) -> ResumeService:
    return ResumeService(db)


def _to_admin_user_item(user: User, company=None) -> AdminUserListItem:
    company_summary = None
    if company is not None:
        company_summary = AdminCompanySummary(
            company_id=company.company_id,
            user_id=company.user_id,
            company_name=company.company_name,
            business_number=company.business_number,
            representative_name=user.name,
            created_at=company.created_at,
            updated_at=company.updated_at,
        )
    item = AdminUserListItem.model_validate(user)
    item.company = company_summary
    return item


@router.get("", response_model=list[AdminUserListItem])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: str | None = None,
    q: str | None = None,
    admin_identifier: str | None = None,
    admin_level: str | None = None,
    name: str | None = None,
    birth_date: str | None = None,
    company_name: str | None = None,
    business_number: str | None = None,
    representative_name: str | None = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> list[AdminUserListItem]:
    user_repo = UserRepository(db)
    rows = user_repo.list_users_for_admin(
        skip=skip,
        limit=limit,
        role=role,
        q=q,
        admin_identifier=admin_identifier,
        admin_level=admin_level,
        name=name,
        birth_date=birth_date,
        company_name=company_name,
        business_number=business_number,
        representative_name=representative_name,
    )
    return [_to_admin_user_item(user, company) for user, company in rows]


@router.get("/resumes/{resume_id}", response_model=ResumeDetail)
def get_user_resume_detail(
    resume_id: int,
    current_admin: User = Depends(get_current_admin_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    try:
        resume = resume_service.get_resume_for_admin(resume_id)
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )

    structured_projects = resume_service.get_structured_projects(resume_id)
    structured_cls = resume_service.get_structured_cover_letter_sections(resume_id)

    detail = ResumeDetail.model_validate(resume)
    detail.structured_projects = [
        ResumeProjectResponse.model_validate(p) for p in structured_projects
    ]
    detail.structured_cover_letter_sections = [
        ResumeCoverLetterSectionResponse.model_validate(s) for s in structured_cls
    ]
    return detail


@router.patch("/resumes/{resume_id}", response_model=ResumeDetail)
def update_user_resume_detail(
    resume_id: int,
    payload: ResumeUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeDetail:
    parsed_data = (
        payload.parsed_data.model_dump(mode="json")
        if payload.parsed_data is not None
        else None
    )
    structured_projects = (
        [p.model_dump(mode="json") for p in payload.structured_projects]
        if payload.structured_projects is not None
        else None
    )

    try:
        resume = resume_service.update_resume_content_for_admin(
            resume_id,
            actor_id=current_admin.user_id,
            title=payload.title,
            raw_text=payload.raw_text,
            parsed_data=parsed_data,
            structured_projects=structured_projects,
            structured_cover_letter_sections=payload.structured_cover_letter_sections,
            request_ip=get_client_ip(request),
        )
    except ResumeNotFoundError:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.RESUME_NOT_FOUND,
            message="이력서를 찾을 수 없습니다.",
        )

    structured_projects_rows = resume_service.get_structured_projects(resume_id)
    structured_cls_rows = resume_service.get_structured_cover_letter_sections(resume_id)

    detail = ResumeDetail.model_validate(resume)
    detail.structured_projects = [
        ResumeProjectResponse.model_validate(p) for p in structured_projects_rows
    ]
    detail.structured_cover_letter_sections = [
        ResumeCoverLetterSectionResponse.model_validate(s) for s in structured_cls_rows
    ]
    return detail


@router.get("/resumes/{resume_id}/file")
def get_user_resume_file(
    resume_id: int,
    current_admin: User = Depends(get_current_admin_user),
    resume_service: ResumeService = Depends(get_resume_service),
) -> FileResponse:
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
            message="이력서 파일을 저장소에서 찾을 수 없습니다.",
        )

    return FileResponse(
        path=resume.file_path,
        media_type=resume.content_type,
        filename=resume.original_filename,
    )


@router.get("/{user_id}", response_model=AdminUserDetail)
def get_user_detail(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    resume_service: ResumeService = Depends(get_resume_service),
) -> AdminUserDetail:
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.USER_NOT_FOUND,
            message="사용자를 찾을 수 없습니다.",
        )

    company = CompanyRepository(db).get_by_user_id(user_id)

    resumes = resume_service.list_resumes(user_id)
    return AdminUserDetail(
        user=_to_admin_user_item(user, company),
        resumes=[ResumeListItem.model_validate(r) for r in resumes],
    )
