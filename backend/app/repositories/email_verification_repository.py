"""
EmailVerification 테이블 DB 접근 계층
"""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.email_verification import EmailVerification


class EmailVerificationRepository:
    """이메일 인증 코드 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        email: str,
        purpose: str,
        code_hash: str,
        expires_at: datetime,
    ) -> EmailVerification:
        record = EmailVerification(
            email=email,
            purpose=purpose,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def delete_unused_by_email(self, email: str, purpose: str) -> None:
        """같은 이메일/용도의 미사용 코드를 정리한다(중복 발급 방지)."""
        stmt = (
            delete(EmailVerification)
            .where(EmailVerification.email == email)
            .where(EmailVerification.purpose == purpose)
            .where(EmailVerification.is_used.is_(False))
        )
        self.db.execute(stmt)
        self.db.flush()

    def get_latest_by_email_and_purpose(
        self, *, email: str, purpose: str
    ) -> EmailVerification | None:
        """이메일과 용도 기준으로 가장 최근 발급 기록을 조회한다."""
        stmt = (
            select(EmailVerification)
            .where(EmailVerification.email == email)
            .where(EmailVerification.purpose == purpose)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def get_latest_active(
        self, *, email: str, purpose: str
    ) -> EmailVerification | None:
        """이메일과 용도 기준으로 가장 최근 활성 코드를 조회한다."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(EmailVerification)
            .where(EmailVerification.email == email)
            .where(EmailVerification.purpose == purpose)
            .where(EmailVerification.is_used.is_(False))
            .where(EmailVerification.expires_at > now)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def get_valid(
        self, *, email: str, purpose: str, code_hash: str
    ) -> EmailVerification | None:
        """이메일·용도·코드 해시가 일치하는 미사용·미만료 코드를 조회한다."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(EmailVerification)
            .where(EmailVerification.email == email)
            .where(EmailVerification.purpose == purpose)
            .where(EmailVerification.code_hash == code_hash)
            .where(EmailVerification.is_used.is_(False))
            .where(EmailVerification.expires_at > now)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def mark_used(self, record: EmailVerification) -> None:
        record.is_used = True
        record.used_at = datetime.now(timezone.utc)
        self.db.flush()

    def record_failed_attempt(self, record: EmailVerification) -> None:
        record.attempt_count = (record.attempt_count or 0) + 1
        record.last_attempt_at = datetime.now(timezone.utc)
        self.db.flush()

    def record_successful_attempt(self, record: EmailVerification) -> None:
        record.last_attempt_at = datetime.now(timezone.utc)
        self.db.flush()

    def expire(self, record: EmailVerification) -> None:
        now = datetime.now(timezone.utc)
        record.expires_at = now
        record.is_used = True
        record.used_at = now
        self.db.flush()
