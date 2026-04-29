"""
Category 테이블 DB 접근 계층
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository:
    """카테고리 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def list(self, include_inactive: bool = False) -> list[Category]:
        stmt = select(Category).where(Category.is_deleted.is_(False))
        if not include_inactive:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.sort_order.asc(), Category.category_id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(
        self,
        category_id: int,
        include_inactive: bool = False,
        include_deleted: bool = False,
    ) -> Category | None:
        stmt = select(Category).where(Category.category_id == category_id)
        if not include_deleted:
            stmt = stmt.where(Category.is_deleted.is_(False))
        if not include_inactive:
            stmt = stmt.where(Category.is_active.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str, include_deleted: bool = False) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        if not include_deleted:
            stmt = stmt.where(Category.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, category_create: CategoryCreate, actor_id: int) -> Category:
        category = Category(
            name=category_create.name,
            slug=category_create.slug,
            description=category_create.description,
            sort_order=category_create.sort_order,
            is_active=category_create.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(category)
        self.db.flush()
        return category

    def update(
        self,
        category: Category,
        category_update: CategoryUpdate,
        actor_id: int,
    ) -> Category:
        update_data = category_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = actor_id
        self.db.flush()
        return category

    def soft_delete(self, category: Category, actor_id: int) -> None:
        category.is_deleted = True
        category.is_active = False
        category.updated_by = actor_id
        self.db.flush()
