"""
Company 테이블 DB 접근 계층
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company


class CompanyRepository:
    """기업회원(회사) DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_dedup_key(self, dedup_key: str) -> Company | None:
        stmt = (
            select(Company)
            .where(Company.dedup_key == dedup_key)
            .where(Company.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user_id(self, user_id: int) -> Company | None:
        stmt = (
            select(Company)
            .where(Company.user_id == user_id)
            .where(Company.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_business_number(self, business_number: str) -> Company | None:
        stmt = (
            select(Company)
            .where(Company.business_number == business_number)
            .where(Company.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(
        self,
        *,
        user_id: int,
        company_name: str | None,
        business_number: str | None,
        dedup_key: str,
    ) -> Company:
        company = Company(
            user_id=user_id,
            company_name=company_name,
            business_number=business_number,
            dedup_key=dedup_key,
        )
        self.db.add(company)
        self.db.flush()
        return company
