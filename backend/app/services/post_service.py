"""
게시글 CRUD 비즈니스 로직
"""

from sqlalchemy.orm import Session

from app.models.post import Post
from app.repositories.category_repository import CategoryRepository
from app.repositories.post_repository import PostRepository
from app.schemas.post import PostCreate, PostUpdate


class PostNotFoundError(Exception):
    """게시글을 찾을 수 없음"""


class PostPermissionError(Exception):
    """게시글 작업 권한 없음"""


class PostCategoryNotFoundError(Exception):
    """게시글 카테고리를 찾을 수 없음"""


class PostService:
    """게시글 관련 비즈니스 로직"""

    def __init__(self, db: Session):
        self.db = db
        self.category_repository = CategoryRepository(db)
        self.post_repository = PostRepository(db)

    def list_posts(
        self,
        offset: int = 0,
        limit: int = 20,
        category_id: int | None = None,
    ) -> list[Post]:
        return self.post_repository.list(
            offset=offset,
            limit=limit,
            category_id=category_id,
        )

    def get_post(self, post_id: int) -> Post:
        post = self.post_repository.get_by_id(post_id)
        if post is None:
            raise PostNotFoundError
        return post

    def create_post(self, post_create: PostCreate, author_id: int) -> Post:
        self._ensure_active_category(post_create.category_id)
        post = self.post_repository.create(post_create, author_id=author_id)
        self.db.commit()
        self.db.refresh(post)
        return post

    def update_post(self, post_id: int, post_update: PostUpdate, updater_id: int) -> Post:
        post = self.get_post(post_id)
        if post_update.category_id is not None:
            self._ensure_active_category(post_update.category_id)
        post = self.post_repository.update(post, post_update, updater_id=updater_id)
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete_post(self, post_id: int, deleter_id: int) -> None:
        post = self.get_post(post_id)
        self.post_repository.soft_delete(post, deleter_id=deleter_id)
        self.db.commit()

    def _ensure_active_category(self, category_id: int) -> None:
        category = self.category_repository.get_by_id(category_id)
        if category is None:
            raise PostCategoryNotFoundError
