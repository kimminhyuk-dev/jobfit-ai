"""
기업회원 계정 자동 생성(provisioning) 비즈니스 로직.

크롤링 공고를 수집할 때, 또는 지원이 들어올 때 해당 회사의 기업계정을
보장(ensure)한다. 같은 회사는 사업자번호 우선, 없으면 회사명으로 식별한다.

주의(포트폴리오 데모 한정):
- 크롤링 회사는 실제로 가입한 적이 없으므로 로그인 계정을 합성 이메일로
  자동 생성하고, 데모용 공통 비밀번호(admin1234)를 사용한다.
- 실서비스에서는 회사가 직접 가입(사업자 인증)하는 방식으로 대체해야 한다.
"""

from __future__ import annotations

import hashlib
import logging
import re
from functools import lru_cache

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User
from app.repositories.company_repository import CompanyRepository

logger = logging.getLogger(__name__)

COMPANY_DEMO_PASSWORD = "admin1234"
COMPANY_EMAIL_DOMAIN = "company.jobfit.local"


def compute_dedup_key(
    business_number: str | None,
    company_name: str | None,
) -> str | None:
    """회사 식별 키를 만든다. 사업자번호 우선, 없으면 회사명."""
    digits = re.sub(r"[^0-9]", "", business_number or "")
    if digits:
        return f"bn:{digits}"
    name = (company_name or "").strip()
    if name:
        return f"nm:{name}"
    return None


@lru_cache(maxsize=1)
def _demo_password_hash() -> str:
    """데모 공통 비밀번호 해시. bcrypt가 느리므로 프로세스당 1회만 계산한다."""
    return hash_password(COMPANY_DEMO_PASSWORD)


def _synthetic_email(dedup_key: str) -> str:
    """식별 키로부터 ASCII 안전한 고유 로그인 이메일을 만든다."""
    digest = hashlib.sha1(dedup_key.encode("utf-8")).hexdigest()[:16]
    return f"company.{digest}@{COMPANY_EMAIL_DOMAIN}"


class CompanyProvisioningService:
    """회사명/사업자번호로 기업계정을 보장한다."""

    def __init__(self, db: Session):
        self.db = db
        self.company_repository = CompanyRepository(db)

    def ensure_company(
        self,
        *,
        company_name: str | None,
        business_number: str | None,
    ) -> Company | None:
        """
        해당 회사의 기업계정을 보장하고 Company를 반환한다.
        식별 정보가 전혀 없으면 None을 반환한다.
        자체적으로 commit 한다.
        """
        dedup_key = compute_dedup_key(business_number, company_name)
        if dedup_key is None:
            return None

        existing = self.company_repository.get_by_dedup_key(dedup_key)
        if existing is not None:
            return existing

        try:
            user = User(
                email=_synthetic_email(dedup_key),
                password=_demo_password_hash(),
                name=(company_name or "기업회원")[:50],
                role="COMPANY",
                status="ACTIVE",
            )
            self.db.add(user)
            self.db.flush()
            company = self.company_repository.create(
                user_id=user.user_id,
                company_name=(company_name or None),
                business_number=(business_number or None),
                dedup_key=dedup_key,
            )
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError:
            # 동시 수집 등으로 이미 만들어진 경우: 롤백 후 재조회한다.
            self.db.rollback()
            return self.company_repository.get_by_dedup_key(dedup_key)
