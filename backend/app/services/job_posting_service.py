"""
채용공고 저장 비즈니스 로직
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.batch_job_run import BatchJobRun
from app.models.job_posting import JobPosting
from app.repositories.job_posting_repository import JobPostingRepository
from app.services.company_provisioning_service import CompanyProvisioningService

logger = logging.getLogger(__name__)


class JobPostingSaveError(Exception):
    """채용공고 저장 실패"""


class JobPostingService:
    """채용공고 관련 비즈니스 로직."""

    def __init__(self, db: Session):
        self.db = db
        self.job_posting_repository = JobPostingRepository(db)
        self.company_provisioning_service = CompanyProvisioningService(db)

    def _ensure_company_account(
        self,
        company_name: str | None,
        business_number: str | None,
    ) -> None:
        """공고 회사의 기업계정을 보장한다. 실패해도 공고 저장은 유지한다."""
        try:
            self.company_provisioning_service.ensure_company(
                company_name=company_name,
                business_number=business_number,
            )
        except Exception as exc:  # noqa: BLE001 - 회사 계정 생성 실패를 격리
            self.db.rollback()
            logger.warning(
                "기업계정 자동 생성 실패 (company_name=%s): %s",
                company_name,
                exc,
            )

    def save_from_work24(
        self,
        run: BatchJobRun,
        work24_data: dict[str, Any],
        data_source: str = "PRODUCTION",
    ) -> tuple[JobPosting, str]:
        """Work24 목록 API 응답 한 건을 저장한다."""
        source_job_id = _required_text(work24_data, "source_job_id")
        title = _required_text(work24_data, "title")

        mapped_data: dict[str, Any] = {
            "source_url": _text_or_none(work24_data.get("source_url")),
            "mobile_url": _text_or_none(work24_data.get("mobile_url")),
            "company_name": _text_or_none(work24_data.get("company_name")),
            "business_number": _text_or_none(work24_data.get("business_number")),
            "industry": _text_or_none(work24_data.get("industry")),
            "title": title,
            "location": _text_or_none(work24_data.get("location")),
            "location_address": _text_or_none(work24_data.get("location_address")),
            "career_level": _text_or_none(work24_data.get("career_level")),
            "education": _text_or_none(work24_data.get("education")),
            "employment_type_code": _text_or_none(
                work24_data.get("employment_type_code")
            ),
            "work_schedule": _text_or_none(work24_data.get("work_schedule")),
            "salary_type": _text_or_none(work24_data.get("salary_type")),
            "salary_text": _text_or_none(work24_data.get("salary_text")),
            "min_salary": _parse_int(work24_data.get("min_salary")),
            "max_salary": _parse_int(work24_data.get("max_salary")),
            "posted_at": _parse_work24_datetime(work24_data.get("posted_at")),
            "deadline": _parse_work24_datetime(work24_data.get("deadline")),
            "source_updated_at": _parse_work24_datetime(
                work24_data.get("source_updated_at")
            ),
            "raw_response": _json_safe(work24_data.get("raw_response") or work24_data),
            "data_source": data_source,
            "status": "OPEN",
            "collection_status": "COLLECTED",
            "embedding_status": "PENDING",
            "collect_run_id": run.run_id,
        }
        # TODO: 상세 API의 jobCont는 raw_content에, keywordList.srchKeywordNm은
        # parsed_skills에 매핑한다. Phase 2 목록 수집에서는 기존 상세값을 덮지 않는다.
        mapped_data["hash_signature"] = _hash_signature(mapped_data)

        try:
            posting, inserted, skipped = self.job_posting_repository.upsert(
                source="WORK24",
                source_job_id=source_job_id,
                data=mapped_data,
            )
            self.db.commit()
            self.db.refresh(posting)
        except Exception as exc:
            self.db.rollback()
            raise JobPostingSaveError("채용공고 저장에 실패했습니다.") from exc

        self._ensure_company_account(
            mapped_data.get("company_name"),
            mapped_data.get("business_number"),
        )

        if inserted:
            return posting, "INSERTED"
        if skipped:
            return posting, "SKIPPED"
        return posting, "UPDATED"

    def save_from_alio(
        self,
        run: BatchJobRun,
        alio_data: dict[str, Any],
        data_source: str = "PRODUCTION",
    ) -> tuple[JobPosting, str]:
        """ALIO 채용정보 목록/상세 정규화 응답 한 건을 저장한다."""
        source_job_id = _required_text(alio_data, "source_job_id")
        title = _required_text(alio_data, "title")

        mapped_data: dict[str, Any] = {
            "source_url": _text_or_none(alio_data.get("source_url")),
            "company_name": _text_or_none(alio_data.get("company_name")),
            "title": title,
            "location": _text_or_none(alio_data.get("location")),
            "location_code": _text_or_none(alio_data.get("location_code")),
            "career_level": _text_or_none(alio_data.get("career_level")),
            "career_level_code": _text_or_none(alio_data.get("career_level_code")),
            "education": _text_or_none(alio_data.get("education")),
            "education_code": _text_or_none(alio_data.get("education_code")),
            "employment_type": _text_or_none(alio_data.get("employment_type")),
            "employment_type_code": _text_or_none(
                alio_data.get("employment_type_code")
            ),
            "ncs_category": _text_or_none(alio_data.get("ncs_category")),
            "ncs_category_code": _text_or_none(alio_data.get("ncs_category_code")),
            "organization_type": _text_or_none(alio_data.get("organization_type")),
            "organization_type_code": _text_or_none(
                alio_data.get("organization_type_code")
            ),
            "organization_category": _text_or_none(
                alio_data.get("organization_category")
            ),
            "organization_category_code": _text_or_none(
                alio_data.get("organization_category_code")
            ),
            "ministry": _text_or_none(alio_data.get("ministry")),
            "ministry_code": _text_or_none(alio_data.get("ministry_code")),
            "posted_at": _parse_datetime(alio_data.get("posted_at")),
            "deadline": _parse_datetime(alio_data.get("deadline")),
            "updated_from_source_at": _parse_datetime(
                alio_data.get("updated_from_source_at")
            ),
            "raw_content": _text_or_none(alio_data.get("raw_content")),
            "raw_response": _json_safe(alio_data.get("raw_response") or alio_data),
            "parsed_skills": _json_safe(alio_data.get("parsed_skills")),
            "data_source": data_source,
            "status": _text_or_none(alio_data.get("status")) or "OPEN",
            "collection_status": "COLLECTED",
            "embedding_status": "PENDING",
            "collect_run_id": run.run_id,
        }
        mapped_data["hash_signature"] = _hash_signature(mapped_data)

        try:
            posting, inserted, skipped = self.job_posting_repository.upsert(
                source="ALIO",
                source_job_id=source_job_id,
                data=mapped_data,
            )
            self.db.commit()
            self.db.refresh(posting)
        except Exception as exc:
            self.db.rollback()
            raise JobPostingSaveError("ALIO 채용공고 저장에 실패했습니다.") from exc

        self._ensure_company_account(
            mapped_data.get("company_name"),
            mapped_data.get("business_number"),
        )

        if inserted:
            return posting, "INSERTED"
        if skipped:
            return posting, "SKIPPED"
        return posting, "UPDATED"


def _required_text(data: dict[str, Any], key: str) -> str:
    value = _text_or_none(data.get(key))
    if value is None:
        raise JobPostingSaveError(f"필수 채용공고 값이 없습니다: {key}")
    return value


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_int(value: Any) -> int | None:
    text = _text_or_none(value)
    if text is None:
        return None
    normalized = re.sub(r"[^0-9-]", "", text)
    if normalized in {"", "-"}:
        return None
    try:
        return int(normalized)
    except ValueError:
        return None


def _parse_work24_datetime(value: Any) -> datetime | None:
    text = _text_or_none(value)
    if text is None:
        return None

    for length, fmt in ((14, "%Y%m%d%H%M%S"), (12, "%Y%m%d%H%M"), (8, "%Y%m%d")):
        try:
            parsed = datetime.strptime(text[:length], fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_datetime(value: Any) -> datetime | None:
    text = _text_or_none(value)
    if text is None:
        return None

    normalized = text.replace(".", "-").replace("/", "-")
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+0000"
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y%m%d%H%M%S",
        "%Y%m%d",
    ):
        try:
            parsed = datetime.strptime(normalized, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue
    return None


def _hash_signature(data: dict[str, Any]) -> str:
    hash_target = {
        key: value
        for key, value in data.items()
        if key not in {"collect_run_id", "collection_status", "embedding_status"}
    }
    payload = json.dumps(
        _json_safe(hash_target),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
