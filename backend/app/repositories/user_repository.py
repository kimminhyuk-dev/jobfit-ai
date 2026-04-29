"""
User 테이블 DB 접근 계층
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


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

    def create(self, user_create: UserCreate, hashed_password: str, request_ip: str | None) -> User:
        user = User(
            email=str(user_create.email),
            password=hashed_password,
            name=user_create.name,
            created_ip=request_ip,
            updated_ip=request_ip,
        )
        self.db.add(user)
        self.db.flush()
        return user
