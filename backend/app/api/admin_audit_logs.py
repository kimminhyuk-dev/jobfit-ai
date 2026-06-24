"""관리자 감사 로그 조회 API."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.rbac import PERM_AUDIT_VIEW
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit-logs"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    table_name: str | None = Query(default=None, max_length=80),
    actor: int | None = Query(default=None, ge=1),
    action: str | None = Query(default=None, max_length=20),
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _current_user: User = Depends(require_permission(PERM_AUDIT_VIEW)),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """감사 로그를 필터와 페이지 조건으로 조회한다."""
    items, total = AuditLogRepository(db).list_logs(
        table_name=table_name,
        actor_user_id=actor,
        action=action.strip().upper() if action else None,
        start_at=start_at,
        end_at=end_at,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
