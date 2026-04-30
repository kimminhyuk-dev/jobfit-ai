"""
Work24 채용공고 수집 비즈니스 로직
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.batch_job_run import BatchJobRun
from app.repositories.batch_job_run_repository import BatchJobRunRepository
from app.services.job_source_service import (
    JobSourceNotFoundError,
    JobSourceService,
    JobSourceUnavailableError,
    make_blocked_idempotency_key,
)
from app.services.job_posting_service import JobPostingSaveError, JobPostingService
from app.services.job_sources.work24_client import (
    Work24ApiKeyMissingError,
    Work24Client,
    Work24ClientError,
    Work24XmlParseError,
)


class Work24CollectionError(Exception):
    """Work24 수집 실패"""


WORK24_SOURCE_CODE = "WORK24"


class Work24CollectionService:
    """Work24 채용정보 수집을 조율한다."""

    def __init__(self, db: Session):
        self.db = db
        self.batch_job_run_repository = BatchJobRunRepository(db)
        self.job_source_service = JobSourceService(db)
        self.job_posting_service = JobPostingService(db)
        self.work24_client = Work24Client()

    def collect_jobs(
        self,
        params: dict[str, Any],
        triggered_by: str | None,
        idempotency_key: str | None,
    ) -> BatchJobRun:
        """Work24 목록 API에서 채용공고를 수집한다."""
        try:
            self.job_source_service.ensure_collectable(WORK24_SOURCE_CODE)
        except JobSourceUnavailableError as exc:
            return self._record_disabled_run(
                params=params,
                triggered_by=triggered_by,
                idempotency_key=idempotency_key,
                source_status=exc.status,
                error_message=exc.message,
            )
        except JobSourceNotFoundError as exc:
            return self._record_disabled_run(
                params=params,
                triggered_by=triggered_by,
                idempotency_key=idempotency_key,
                source_status="NOT_FOUND",
                error_message=str(exc),
            )

        duplicate_run = self._find_recent_duplicate_run(idempotency_key)
        if duplicate_run is not None:
            return duplicate_run

        run = self.batch_job_run_repository.create_run(
            job_code="WORK24_COLLECT",
            job_name="Work24 채용정보 수동 수집",
            source=WORK24_SOURCE_CODE,
            trigger_type="MANUAL",
            triggered_by=triggered_by,
            idempotency_key=idempotency_key,
            request_params=params,
        )
        self.db.commit()
        self.db.refresh(run)

        run = self.batch_job_run_repository.mark_running(run.run_id)
        self.db.commit()
        self.db.refresh(run)

        counts = {
            "collected_count": 0,
            "inserted_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "success_count": 0,
            "failed_count": 0,
        }

        final_status = "SUCCESS"
        error: dict[str, str] | None = None

        try:
            self._collect_pages(run, params, counts)
        except Work24ApiKeyMissingError:
            final_status = "FAILED"
            error = {
                "error_code": "JOB_005",
                "error_message": "Work24 채용정보 API 키가 설정되지 않았습니다.",
            }
        except Work24XmlParseError:
            final_status = "FAILED"
            error = {
                "error_code": "JOB_004",
                "error_message": "Work24 XML 응답 파싱에 실패했습니다.",
            }
        except Work24ClientError as exc:
            if "status=429" in str(exc):
                final_status = "RATE_LIMITED"
            else:
                final_status = "FAILED"
            error = {
                "error_code": "JOB_003",
                "error_message": "Work24 외부 API 호출에 실패했습니다.",
            }
        except Exception as exc:
            final_status = "FAILED"
            error = {
                "error_code": "BATCH_001",
                "error_message": "Work24 채용정보 수집 배치가 실패했습니다.",
            }
            self.db.rollback()
            raise Work24CollectionError("Work24 채용정보 수집에 실패했습니다.") from exc
        else:
            final_status = _decide_status(counts)

        run = self.batch_job_run_repository.mark_finished(
            run_id=run.run_id,
            status=final_status,
            counts=counts,
            error=error,
        )
        self.db.commit()
        self.db.refresh(run)
        return run

    def _record_disabled_run(
        self,
        params: dict[str, Any],
        triggered_by: str | None,
        idempotency_key: str | None,
        source_status: str,
        error_message: str,
    ) -> BatchJobRun:
        """WORK24 보류 상태를 외부 호출 없이 배치 실패 이력으로 남긴다."""
        blocked_key = make_blocked_idempotency_key(
            source_code=WORK24_SOURCE_CODE,
            idempotency_key=idempotency_key,
        )
        if blocked_key:
            duplicate_run = self.batch_job_run_repository.find_by_idempotency_key(
                blocked_key
            )
            if duplicate_run is not None:
                return duplicate_run

        request_params = {
            **params,
            "source_status": source_status,
        }
        run = self.batch_job_run_repository.create_run(
            job_code="WORK24_COLLECT",
            job_name="Work24 채용정보 수동 수집",
            source=WORK24_SOURCE_CODE,
            trigger_type="MANUAL",
            triggered_by=triggered_by,
            idempotency_key=blocked_key,
            request_params=request_params,
        )
        self.db.commit()
        self.db.refresh(run)

        run = self.batch_job_run_repository.mark_running(run.run_id)
        self.db.commit()
        self.db.refresh(run)

        run = self.batch_job_run_repository.mark_finished(
            run_id=run.run_id,
            status="BLOCKED",
            counts={
                "collected_count": 0,
                "inserted_count": 0,
                "updated_count": 0,
                "skipped_count": 1,
                "success_count": 0,
                "failed_count": 0,
            },
            error={
                "error_code": "JOB_SOURCE_001",
                "error_message": error_message,
            },
        )
        self.db.commit()
        self.db.refresh(run)
        return run

    def _collect_pages(
        self,
        run: BatchJobRun,
        params: dict[str, Any],
        counts: dict[str, int],
    ) -> None:
        start_page = int(params.get("start_page", 1))
        max_pages = int(params.get("max_pages", 1))
        display = int(params.get("display", 10))

        for page_offset in range(max_pages):
            if page_offset > 0:
                self.work24_client.wait_between_requests()

            wanted_list = self.work24_client.fetch_job_list(
                keyword=params.get("keyword"),
                start_page=start_page + page_offset,
                display=display,
                region=params.get("region"),
                occupation=params.get("occupation"),
            )
            counts["collected_count"] += len(wanted_list)

            for wanted in wanted_list:
                try:
                    _, save_status = self.job_posting_service.save_from_work24(
                        run=run,
                        work24_data=wanted,
                    )
                except JobPostingSaveError:
                    counts["failed_count"] += 1
                    continue

                if save_status == "INSERTED":
                    counts["inserted_count"] += 1
                elif save_status == "UPDATED":
                    counts["updated_count"] += 1
                else:
                    counts["skipped_count"] += 1
                counts["success_count"] += 1

    def _find_recent_duplicate_run(
        self,
        idempotency_key: str | None,
    ) -> BatchJobRun | None:
        if not idempotency_key:
            return None
        run = self.batch_job_run_repository.find_by_idempotency_key(idempotency_key)
        if run is None:
            return None
        created_at = run.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created_at <= timedelta(minutes=5):
            return run
        return None


def _decide_status(counts: dict[str, int]) -> str:
    failed_count = counts["failed_count"]
    if failed_count == 0:
        return "SUCCESS"
    if counts.get("success_count", 0) > 0:
        return "PARTIAL_SUCCESS"
    return "FAILED"
