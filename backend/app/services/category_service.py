"""
카테고리 CRUD 비즈니스 로직
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryNotFoundError(Exception):
    """카테고리를 찾을 수 없음"""


class DuplicateCategorySlugError(Exception):
    """중복 카테고리 slug"""


class CategoryService:
    """카테고리 관련 비즈니스 로직"""

    def __init__(self, db: Session):
        self.db = db
        self.category_repository = CategoryRepository(db)

    def list_categories(self, include_inactive: bool = False) -> list[Category]:
        return self.category_repository.list(include_inactive=include_inactive)

    def get_category(self, category_id: int, include_inactive: bool = False) -> Category:
        category = self.category_repository.get_by_id(
            category_id,
            include_inactive=include_inactive,
        )
        if category is None:
            raise CategoryNotFoundError
        return category

    def create_category(self, category_create: CategoryCreate, actor_id: int) -> Category:
        if self.category_repository.get_by_slug(category_create.slug, include_deleted=True):
            raise DuplicateCategorySlugError

        try:
            category = self.category_repository.create(category_create, actor_id=actor_id)
            self.db.commit()
            self.db.refresh(category)
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateCategorySlugError from exc
        return category

    def update_category(
        self,
        category_id: int,
        category_update: CategoryUpdate,
        actor_id: int,
    ) -> Category:
        category = self.get_category(category_id, include_inactive=True)
        if category_update.slug is not None:
            existing = self.category_repository.get_by_slug(
                category_update.slug,
                include_deleted=True,
            )
            if existing is not None and existing.category_id != category_id:
                raise DuplicateCategorySlugError

        try:
            category = self.category_repository.update(
                category,
                category_update,
                actor_id=actor_id,
            )
            self.db.commit()
            self.db.refresh(category)
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateCategorySlugError from exc
        return category

    def delete_category(self, category_id: int, actor_id: int) -> None:
        category = self.get_category(category_id, include_inactive=True)
        self.category_repository.soft_delete(category, actor_id=actor_id)
        self.db.commit()
