"""
Mock 채용공고 데이터 로더 서비스
backend/data/mock_work24_jobs.json 을 읽어 JobPosting 테이블에 저장한다.
"""

from __future__ import annotations

import json
import os
from typing import Any

from sqlalchemy.orm import Session

from app.models.batch_job_run import BatchJobRun
from app.repositories.batch_job_run_repository import BatchJobRunRepository
from app.services.job_posting_service import JobPostingSaveError, JobPostingService
from app.services.job_sources.work24_client import _normalize_wanted

DEFAULT_FILE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "mock_work24_jobs.json")
)


class MockLoaderError(Exception):
    """Mock 데이터 로드 실패"""


class MockLoaderService:
    """JSON 파일에서 Mock 채용공고를 읽어 data_source='MOCK'으로 저장한다."""

    def __init__(self, db: Session):
        self.db = db
        self.batch_repo = BatchJobRunRepository(db)
        self.job_posting_service = JobPostingService(db)

    def load_mock_data(
        self,
        file_path: str | None = None,
        triggered_by: str = "ADMIN",
    ) -> BatchJobRun:
        resolved_path = file_path or DEFAULT_FILE_PATH

        run = self.batch_repo.create_run(
            job_code="MOCK_LOAD",
            job_name="Mock 채용공고 데이터 로드",
            source="WORK24",
            trigger_type="MANUAL",
            triggered_by=triggered_by,
            idempotency_key=None,
            request_params={"file_path": resolved_path},
        )
        self.db.commit()
        self.db.refresh(run)

        run = self.batch_repo.mark_running(run.run_id)
        self.db.commit()
        self.db.refresh(run)

        counts: dict[str, int] = {
            "collected_count": 0,
            "inserted_count": 0,
            "updated_count": 0,
            "skipped_count": 0,
            "success_count": 0,
            "failed_count": 0,
        }

        try:
            wanted_list = self._load_json(resolved_path)
            counts["collected_count"] = len(wanted_list)

            for wanted_raw in wanted_list:
                normalized = _normalize_wanted(wanted_raw)
                try:
                    _, save_status = self.job_posting_service.save_from_work24(
                        run=run,
                        work24_data=normalized,
                        data_source="MOCK",
                    )
                except JobPostingSaveError:
                    counts["failed_count"] += 1
                    continue

                counts["success_count"] += 1
                if save_status == "INSERTED":
                    counts["inserted_count"] += 1
                elif save_status == "UPDATED":
                    counts["updated_count"] += 1
                else:
                    counts["skipped_count"] += 1

        except MockLoaderError as exc:
            run = self.batch_repo.mark_finished(
                run_id=run.run_id,
                status="FAILED",
                counts=counts,
                error={"error_code": "MOCK_001", "error_message": str(exc)},
            )
            self.db.commit()
            self.db.refresh(run)
            return run
        except Exception as exc:
            self.db.rollback()
            raise MockLoaderError("Mock 데이터 로드 중 예외가 발생했습니다.") from exc

        final_status = _decide_status(counts)
        run = self.batch_repo.mark_finished(
            run_id=run.run_id,
            status=final_status,
            counts=counts,
            error=None,
        )
        self.db.commit()
        self.db.refresh(run)
        return run

    def _load_json(self, file_path: str) -> list[dict[str, Any]]:
        if not os.path.isfile(file_path):
            raise MockLoaderError(
                f"Mock JSON 파일을 찾을 수 없습니다: {file_path}\n"
                "backend/data/mock_work24_jobs.json 파일을 준비하세요.\n"
                '구조: {"wantedRoot": {"wanted": [...]}}'
            )
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            raise MockLoaderError(f"Mock JSON 파일 읽기 실패: {exc}") from exc

        wanted_root = data.get("wantedRoot", {})
        wanted_list = wanted_root.get("wanted", [])
        if isinstance(wanted_list, dict):
            wanted_list = [wanted_list]
        if not isinstance(wanted_list, list):
            raise MockLoaderError("Mock JSON 구조 오류: wantedRoot.wanted 가 배열이어야 합니다.")
        return wanted_list


def _decide_status(counts: dict[str, int]) -> str:
    if counts["failed_count"] == 0:
        return "SUCCESS"
    if counts["success_count"] > 0:
        return "PARTIAL_SUCCESS"
    return "FAILED"
