"""기업회원(Company) API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.company import CompanyDashboardResponse
from app.services.company_service import (
    CompanyAccountNotFoundError,
    CompanyService,
)

router = APIRouter(prefix="/company", tags=["company"])


def get_company_service(db: Session = Depends(get_db)) -> CompanyService:
    """CompanyService dependency."""
    return CompanyService(db)


@router.get("/dashboard", response_model=CompanyDashboardResponse)
def get_company_dashboard(
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
) -> CompanyDashboardResponse:
    """기업회원의 대시보드(받은 지원자 현황 + 통계)를 조회한다."""
    if current_user.role != "COMPANY":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.FORBIDDEN,
            message="기업회원만 접근할 수 있습니다.",
        )
    try:
        return company_service.get_dashboard(current_user.user_id)
    except CompanyAccountNotFoundError as exc:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.COMPANY_NOT_FOUND,
            message="기업 계정 정보를 찾을 수 없습니다.",
        ) from exc
