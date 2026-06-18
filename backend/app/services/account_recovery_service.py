"""
계정 복구(비로그인) 비즈니스 로직.

Java JobFolio의 아이디 찾기 / 비밀번호 재설정 흐름을 이식한다.

- 아이디(이메일) 찾기: 이름+전화로 조회 후 **본인 메일로 발송**. 계정 존재 여부는
  응답으로 노출하지 않는다(항상 동일한 처리).
- 비밀번호 재설정(2단계):
  1) 인증 코드 발송: 6자리 코드 생성 → SHA-256 해시로 저장(5분 만료) → 메일 발송.
  2) 코드 검증 + 임시 비밀번호 발송: 코드 검증 → 임시 비밀번호 생성 → 메일 발송 성공 시
     비밀번호 변경 및 전체 세션 무효화.

보안:
- 인증 코드는 평문 저장하지 않고 해시(SHA-256)만 저장한다.
- 임시 비밀번호/인증 코드 원문은 로그에 남기지 않는다.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    generate_numeric_code,
    generate_temporary_password,
    hash_password,
    hash_token,
)
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailConfigError, EmailSendError, EmailService

logger = logging.getLogger(__name__)

PASSWORD_RESET_PURPOSE = "PASSWORD_RESET"
FIND_EMAIL_PURPOSE = "FIND_EMAIL"
COMPANY_FIND_EMAIL_PURPOSE = "COMPANY_FIND_EMAIL"
PASSWORD_RESET_CODE_TTL_MINUTES = 5
RECOVERY_SEND_RATE_LIMIT_SECONDS = 60
PASSWORD_RESET_MAX_FAILURES = 5


class PasswordResetEmailError(Exception):
    """임시 비밀번호 메일 발송에 실패한 상태(코드 검증은 통과)."""


class RecoveryRateLimitedError(Exception):
    """계정 복구 요청 또는 검증 시도가 제한된 상태."""


def mask_email_for_display(email: str) -> str:
    """화면 표시용 이메일 마스킹. 예: abcd@gmail.com -> ab***@gmail.com"""
    local, separator, domain = email.partition("@")
    visible = local[:2] if local else ""
    masked_local = f"{visible}***" if visible else "***"
    if not separator:
        return masked_local
    return f"{masked_local}@{domain}"


def normalize_business_number(value: str) -> str:
    """사업자등록번호를 숫자만 남긴 형태로 정규화한다."""
    return "".join(ch for ch in (value or "") if ch.isdigit())


def mask_business_number_for_log(value: str) -> str:
    """사업자등록번호 원문을 로그에 남기지 않기 위한 마스킹."""
    digits = normalize_business_number(value)
    if len(digits) != 10:
        return "***"
    return f"{digits[:3]}-**-*****"


class AccountRecoveryService:
    """아이디 찾기 / 비밀번호 재설정 비즈니스 로직."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.email_verification_repository = EmailVerificationRepository(db)
        self.refresh_token_repository = RefreshTokenRepository(db)
        self.email_service = EmailService()

    # ----------------------------------------------------------------- #
    # 아이디(이메일) 찾기 — 본인 메일로 발송, 계정 존재 비노출
    # ----------------------------------------------------------------- #
    def find_email(self, name: str, phone: str) -> str | None:
        """이름+전화가 일치하면 본인 메일로 아이디를 발송한다.

        일치하는 개인회원이 있으면 화면 표시용 마스킹 이메일을 반환하고,
        본인 메일로도 아이디 안내를 발송한다.
        """
        name = (name or "").strip()
        phone_digits = "".join(ch for ch in (phone or "") if ch.isdigit())
        if not name or not phone_digits:
            return None

        rate_key = self._lookup_rate_key("find-email", f"{name}:{phone_digits}")
        self._ensure_send_allowed(rate_key, FIND_EMAIL_PURPOSE)
        user = self.user_repository.find_by_name_and_phone(name, phone_digits)
        self._create_send_marker(rate_key, FIND_EMAIL_PURPOSE)
        if user is None:
            return None

        reg_date = (
            user.created_at.strftime("%Y-%m-%d") if user.created_at else None
        )
        try:
            self.email_service.send_found_id_email(user.email, user.email, reg_date)
        except (EmailConfigError, EmailSendError):
            # 존재 비노출 정책상 호출자에게 실패를 드러내지 않는다(로그만 남김).
            logger.warning("find_email: 일치 계정 메일 발송 실패 (마스킹 로그만 기록)")
        return mask_email_for_display(user.email)

    def find_company_email(self, name: str, business_number: str) -> str | None:
        """담당자명+사업자번호가 일치하면 기업 가입 이메일을 안내한다."""
        name = (name or "").strip()
        business_digits = normalize_business_number(business_number)
        if not name or len(business_digits) != 10:
            return None

        rate_key = self._lookup_rate_key(
            "company-find-email",
            f"{name}:{business_digits}",
        )
        self._ensure_send_allowed(rate_key, COMPANY_FIND_EMAIL_PURPOSE)
        user = self.user_repository.find_company_by_name_and_business_number(
            name,
            business_digits,
        )
        self._create_send_marker(rate_key, COMPANY_FIND_EMAIL_PURPOSE)
        if user is None:
            return None

        reg_date = (
            user.created_at.strftime("%Y-%m-%d") if user.created_at else None
        )
        try:
            self.email_service.send_found_id_email(user.email, user.email, reg_date)
        except (EmailConfigError, EmailSendError):
            logger.warning(
                "find_company_email: mail send failed for business=%s",
                mask_business_number_for_log(business_digits),
            )
        return mask_email_for_display(user.email)

    # ----------------------------------------------------------------- #
    # 비밀번호 재설정 1단계 - 인증 코드 발송, 계정 존재 비노출
    # ----------------------------------------------------------------- #
    def request_password_reset(self, email: str) -> None:
        """등록된 이메일이면 6자리 인증 코드를 발송한다(존재 비노출)."""
        email = (email or "").strip()
        if not email:
            return

        self._ensure_send_allowed(email, PASSWORD_RESET_PURPOSE)
        user = self.user_repository.get_by_email(email)
        if user is None:
            self._create_send_marker(email, PASSWORD_RESET_PURPOSE)
            return

        self._send_password_reset_code(email)

    def request_company_password_reset(
        self,
        name: str,
        business_number: str,
        email: str,
    ) -> None:
        """기업 계정의 비밀번호 재설정 코드를 발송한다(계정 존재 비노출)."""
        name = (name or "").strip()
        business_digits = normalize_business_number(business_number)
        email = (email or "").strip()
        if not name or len(business_digits) != 10 or not email:
            return

        self._ensure_send_allowed(email, PASSWORD_RESET_PURPOSE)
        user = self.user_repository.find_company_by_name_business_number_and_email(
            name=name,
            business_number_digits=business_digits,
            email=email,
        )
        if user is None:
            self._create_send_marker(email, PASSWORD_RESET_PURPOSE)
            return

        self._send_password_reset_code(email)

    def _send_password_reset_code(self, email: str) -> None:
        """비밀번호 재설정 인증 코드를 만들고 메일을 발송한다."""
        code = generate_numeric_code(6)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=PASSWORD_RESET_CODE_TTL_MINUTES
        )

        self.email_verification_repository.delete_unused_by_email(
            email, PASSWORD_RESET_PURPOSE
        )
        self.email_verification_repository.create(
            email=email,
            purpose=PASSWORD_RESET_PURPOSE,
            code_hash=hash_token(code),
            expires_at=expires_at,
        )
        self.db.commit()

        try:
            self.email_service.send_verification_code(email, code)
        except (EmailConfigError, EmailSendError):
            logger.warning("request_password_reset: 인증 코드 메일 발송 실패")

    # ----------------------------------------------------------------- #
    # 비밀번호 재설정 2단계 — 코드 검증 후 임시 비밀번호 발송
    # ----------------------------------------------------------------- #
    def confirm_password_reset(self, email: str, code: str) -> bool:
        """코드를 검증하고, 임시 비밀번호를 발송한 뒤 비밀번호를 변경한다.

        반환값:
        - False: 코드가 올바르지 않거나 만료됨.
        - True: 임시 비밀번호 발송 + 비밀번호 변경 완료.

        메일 발송 실패 시(코드는 유효) 비밀번호를 바꾸지 않고 PasswordResetEmailError 를
        던진다(임시 비밀번호를 받지 못한 채 계정이 잠기는 것을 방지).
        """
        email = (email or "").strip()
        code = (code or "").strip()
        if not email or not code:
            return False

        record = self.email_verification_repository.get_latest_active(
            email=email,
            purpose=PASSWORD_RESET_PURPOSE,
        )
        if record is None:
            return False

        if record.code_hash != hash_token(code):
            self.email_verification_repository.record_failed_attempt(record)
            if record.attempt_count >= PASSWORD_RESET_MAX_FAILURES:
                self.email_verification_repository.expire(record)
            self.db.commit()
            return False

        user = self.user_repository.get_by_email(email)
        if user is None:
            self.email_verification_repository.record_failed_attempt(record)
            if record.attempt_count >= PASSWORD_RESET_MAX_FAILURES:
                self.email_verification_repository.expire(record)
            self.db.commit()
            return False

        temporary_password = generate_temporary_password(12)

        # 메일을 먼저 보내고, 성공해야 비밀번호를 실제로 변경한다(잠김 방지).
        try:
            self.email_verification_repository.record_successful_attempt(record)
            self.email_service.send_temporary_password(email, temporary_password)
        except (EmailConfigError, EmailSendError) as exc:
            self.db.rollback()
            raise PasswordResetEmailError from exc

        self.user_repository.update_password(user, hash_password(temporary_password))
        self.email_verification_repository.mark_used(record)
        # 비밀번호 변경 시 모든 세션 강제 만료
        self.refresh_token_repository.revoke_all_by_user(user.user_id)
        self.db.commit()
        return True

    def _ensure_send_allowed(self, key: str, purpose: str) -> None:
        latest = self.email_verification_repository.get_latest_by_email_and_purpose(
            email=key,
            purpose=purpose,
        )
        if latest is not None and self._is_within_seconds(
            latest.created_at,
            RECOVERY_SEND_RATE_LIMIT_SECONDS,
        ):
            raise RecoveryRateLimitedError

    def _create_send_marker(self, key: str, purpose: str) -> None:
        self.email_verification_repository.delete_unused_by_email(key, purpose)
        self.email_verification_repository.create(
            email=key,
            purpose=purpose,
            code_hash=hash_token(secrets.token_urlsafe(32)),
            expires_at=datetime.now(timezone.utc) + timedelta(
                minutes=PASSWORD_RESET_CODE_TTL_MINUTES
            ),
        )
        self.db.commit()

    def _lookup_rate_key(self, prefix: str, value: str) -> str:
        return f"{prefix}:{hash_token(value)[:64]}"

    def _is_within_seconds(
        self,
        value: datetime | None,
        seconds: int,
    ) -> bool:
        if value is None:
            return False
        now = datetime.now(timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return now - value < timedelta(seconds=seconds)
