"""
User 테이블 DB 접근 계층
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User
from app.schemas.user import UserCreate

# update()로 변경 가능한 프로필 필드 화이트리스트
_PROFILE_FIELDS = frozenset(
    {"birth_date", "phone", "gender", "zipcode", "address1", "address2", "tech_stack"}
)


class UserRepository:
    """회원 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int, include_deleted: bool = False) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        if not include_deleted:
            stmt = stmt.where(User.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        stmt = select(User).where(User.email == email)
        if not include_deleted:
            stmt = stmt.where(User.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def count_total(self) -> int:
        stmt = select(func.count()).select_from(User).where(User.is_deleted.is_(False))
        return int(self.db.execute(stmt).scalar_one())

    def count_today(self) -> int:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.is_deleted.is_(False))
            .where(User.created_at >= today_start)
        )
        return int(self.db.execute(stmt).scalar_one())

    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = (
            select(User)
            .where(User.is_deleted.is_(False))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_users_for_admin(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        role: str | None = None,
        q: str | None = None,
        admin_identifier: str | None = None,
        admin_level: str | None = None,
        name: str | None = None,
        birth_date: str | None = None,
        company_name: str | None = None,
        business_number: str | None = None,
        representative_name: str | None = None,
    ) -> list[tuple[User, Company | None]]:
        stmt = (
            select(User, Company)
            .outerjoin(
                Company,
                (Company.user_id == User.user_id) & (Company.is_deleted.is_(False)),
            )
            .where(User.is_deleted.is_(False))
        )

        if role:
            stmt = stmt.where(User.role == role)
        if admin_level:
            stmt = stmt.where(User.admin_level == admin_level)
        if admin_identifier:
            pattern = f"%{admin_identifier.strip()}%"
            stmt = stmt.where(
                or_(
                    cast(User.user_id, String).ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        if name:
            stmt = stmt.where(User.name.ilike(f"%{name.strip()}%"))
        if birth_date:
            stmt = stmt.where(cast(User.birth_date, String).ilike(f"%{birth_date.strip()}%"))
        if company_name:
            stmt = stmt.where(Company.company_name.ilike(f"%{company_name.strip()}%"))
        if business_number:
            digits = "".join(ch for ch in business_number if ch.isdigit())
            pattern = f"%{digits or business_number.strip()}%"
            stmt = stmt.where(Company.business_number.ilike(pattern))
        if representative_name:
            stmt = stmt.where(User.name.ilike(f"%{representative_name.strip()}%"))
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    cast(User.user_id, String).ilike(pattern),
                    User.email.ilike(pattern),
                    User.name.ilike(pattern),
                    cast(User.birth_date, String).ilike(pattern),
                    User.admin_level.ilike(pattern),
                    Company.company_name.ilike(pattern),
                    Company.business_number.ilike(pattern),
                )
            )

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).all())

    def update(
        self,
        user: User,
        name: str | None,
        hashed_password: str | None,
        request_ip: str | None,
        profile_changes: dict[str, Any] | None = None,
    ) -> User:
        if name is not None:
            user.name = name
        if hashed_password is not None:
            user.password = hashed_password
        for field, value in (profile_changes or {}).items():
            if field in _PROFILE_FIELDS:
                setattr(user, field, value)
        user.updated_by = user.user_id
        user.updated_ip = request_ip
        self.db.flush()
        return user

    def soft_delete(self, user: User, request_ip: str | None) -> User:
        user.is_deleted = True
        user.updated_by = user.user_id
        user.updated_ip = request_ip
        self.db.flush()
        return user

    def create(self, user_create: UserCreate, hashed_password: str, request_ip: str | None) -> User:
        user = User(
            email=str(user_create.email),
            password=hashed_password,
            name=user_create.name,
            birth_date=user_create.birth_date,
            phone=user_create.phone,
            gender=user_create.gender,
            zipcode=user_create.zipcode,
            address1=user_create.address1,
            address2=user_create.address2,
            tech_stack=user_create.tech_stack,
            created_ip=request_ip,
            updated_ip=request_ip,
        )
        self.db.add(user)
        self.db.flush()
        return user
