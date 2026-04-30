"""
BatchJobRun 테이블 DB 접근 계층
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.batch_job_run import BatchJobRun


class BatchJobRunRepository:
    """배치 실행 이력 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def find_by_idempotency_key(self, key: str) -> BatchJobRun | None:
        stmt = (
            select(BatchJobRun)
            .where(BatchJobRun.idempotency_key == key)
            .where(BatchJobRun.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, run_id: int) -> BatchJobRun | None:
        stmt = (
            select(BatchJobRun)
            .where(BatchJobRun.run_id == run_id)
            .where(BatchJobRun.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_run(
        self,
        job_code: str,
        job_name: str,
        source: str | None,
        trigger_type: str,
        triggered_by: str | None,
        idempotency_key: str | None,
        request_params: dict[str, Any] | None,
    ) -> BatchJobRun:
        run = BatchJobRun(
            job_code=job_code,
            job_name=job_name,
            source=source,
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            idempotency_key=idempotency_key,
            request_params=request_params,
            status="READY",
        )
        self.db.add(run)
        self.db.flush()
        return run

    def mark_running(self, run_id: int) -> BatchJobRun:
        run = self._get_required(run_id)
        run.status = "RUNNING"
        run.started_at = datetime.now(timezone.utc)
        self.db.flush()
        return run

    def mark_finished(
        self,
        run_id: int,
        status: str,
        counts: dict[str, int],
        error: dict[str, str] | None,
    ) -> BatchJobRun:
        run = self._get_required(run_id)
        run.status = status
        run.ended_at = datetime.now(timezone.utc)
        run.elapsed_ms = _elapsed_ms(run.started_at, run.ended_at)
        run.collected_count = counts.get("collected_count", 0)
        run.inserted_count = counts.get("inserted_count", 0)
        run.updated_count = counts.get("updated_count", 0)
        run.skipped_count = counts.get("skipped_count", 0)
        run.success_count = counts.get(
            "success_count",
            run.inserted_count + run.updated_count + run.skipped_count,
        )
        run.failed_count = counts.get("failed_count", 0)
        run.error_code = error.get("error_code") if error else None
        run.error_message = error.get("error_message") if error else None
        self.db.flush()
        return run

    def _get_required(self, run_id: int) -> BatchJobRun:
        run = self.get_by_id(run_id)
        if run is None:
            raise LookupError("배치 실행 이력을 찾을 수 없습니다.")
        return run


def _elapsed_ms(started_at: datetime | None, ended_at: datetime) -> int | None:
    if started_at is None:
        return None
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return int((ended_at - started_at).total_seconds() * 1000)
