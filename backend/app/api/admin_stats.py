from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin_stats import AdminStatsResponse
from app.services.admin_stats_service import AdminStatsService

router = APIRouter(prefix="/admin", tags=["admin-stats"])


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
) -> AdminStatsResponse:
    """관리자 대시보드 통계 요약을 반환한다."""
    return AdminStatsService(db).get_stats()
