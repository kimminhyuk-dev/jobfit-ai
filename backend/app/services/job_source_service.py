"""
채용공고 수집원 상태 관리 서비스
"""

from __future__ import annotations

import hashlib
from enum import StrEnum

from sqlalchemy.orm import Session

from app.models.job_source import JobSource
from app.repositories.job_source_repository import JobSourceRepository


class JobSourceStatus(StrEnum):
    """채용공고 수집원 운영 상태."""

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    DEPRECATED = "DEPRECATED"


class JobSourceNotFoundError(Exception):
    """채용공고 수집원을 찾을 수 없음"""


class JobSourceUnavailableError(Exception):
    """채용공고 수집원이 현재 수집 가능하지 않음"""

    def __init__(self, source: JobSource):
        self.source_code = source.source_code
        self.status = source.status
        self.disabled_reason = source.disabled_reason
        super().__init__(self.message)

    @property
    def message(self) -> str:
        if self.disabled_reason:
            return self.disabled_reason
        return f"{self.source_code} 수집원은 현재 {self.status} 상태입니다."


class JobSourceService:
    """채용공고 수집원의 상태를 조회하고 수집 가능 여부를 판단한다."""

    def __init__(self, db: Session):
        self.job_source_repository = JobSourceRepository(db)

    def get_source_or_raise(self, source_code: str) -> JobSource:
        source = self.job_source_repository.get_by_code(source_code)
        if source is None:
            raise JobSourceNotFoundError(f"{source_code} 수집원을 찾을 수 없습니다.")
        return source

    def ensure_collectable(self, source_code: str) -> JobSource:
        source = self.get_source_or_raise(source_code)
        if source.status != JobSourceStatus.ACTIVE:
            raise JobSourceUnavailableError(source)
        return source


def make_blocked_idempotency_key(source_code: str, idempotency_key: str | None) -> str | None:
    """비활성 수집원 차단 결과 전용 idempotency key를 만든다."""
    if not idempotency_key:
        return None
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    return f"blocked:{source_code}:{digest}"
