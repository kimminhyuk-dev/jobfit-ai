"""감사 로그 저장과 조회를 담당한다."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Connection, func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """감사 로그 DB 접근 계층."""

    def __init__(self, db: Session):
        self.db = db

    def list_logs(
        self,
        *,
        table_name: str | None = None,
        actor_user_id: int | None = None,
        action: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        """필터와 페이지 조건으로 감사 로그를 조회한다."""
        stmt = select(AuditLog)
        if table_name:
            stmt = stmt.where(AuditLog.table_name == table_name)
        if actor_user_id is not None:
            stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if start_at:
            stmt = stmt.where(AuditLog.created_at >= start_at)
        if end_at:
            stmt = stmt.where(AuditLog.created_at <= end_at)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(self.db.execute(total_stmt).scalar_one())

        offset = (page - 1) * page_size
        items = self.db.execute(
            stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset)
            .limit(page_size)
        ).scalars().all()
        return list(items), total


def record_audit(
    db: Session,
    *,
    table_name: str,
    record_id: int | str,
    action: str,
    actor_user_id: int | None,
    actor_ip: str | None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    summary: str | None = None,
) -> AuditLog:
    """세션 안에서 감사 로그를 남긴다."""
    audit_log = AuditLog(
        table_name=table_name,
        record_id=str(record_id),
        action=action,
        actor_user_id=actor_user_id,
        actor_ip=actor_ip,
        before_data=before_data,
        after_data=after_data,
        summary=summary,
    )
    db.add(audit_log)
    return audit_log


def record_audit_with_connection(
    connection: Connection,
    *,
    table_name: str,
    record_id: int | str,
    action: str,
    actor_user_id: int | None,
    actor_ip: str | None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    summary: str | None = None,
) -> None:
    """ORM 이벤트 내부에서 같은 트랜잭션으로 감사 로그를 남긴다."""
    connection.execute(
        AuditLog.__table__.insert().values(
            table_name=table_name,
            record_id=str(record_id),
            action=action,
            actor_user_id=actor_user_id,
            actor_ip=actor_ip,
            before_data=before_data,
            after_data=after_data,
            summary=summary,
        )
    )
