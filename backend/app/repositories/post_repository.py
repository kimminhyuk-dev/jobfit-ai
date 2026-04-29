"""
Post 테이블 DB 접근 계층
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate


class PostRepository:
    """게시글 DB 작업을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        offset: int = 0,
        limit: int = 20,
        category_id: int | None = None,
    ) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.is_deleted.is_(False))
            .order_by(Post.post_id.desc())
            .offset(offset)
            .limit(limit)
        )
        if category_id is not None:
            stmt = stmt.where(Post.category_id == category_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, post_id: int, include_deleted: bool = False) -> Post | None:
        stmt = select(Post).where(Post.post_id == post_id)
        if not include_deleted:
            stmt = stmt.where(Post.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, post_create: PostCreate, author_id: int) -> Post:
        post = Post(
            author_id=author_id,
            category_id=post_create.category_id,
            title=post_create.title,
            content=post_create.content,
            created_by=author_id,
            updated_by=author_id,
        )
        self.db.add(post)
        self.db.flush()
        return post

    def update(self, post: Post, post_update: PostUpdate, updater_id: int) -> Post:
        update_data = post_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)
        post.updated_by = updater_id
        self.db.flush()
        return post

    def soft_delete(self, post: Post, deleter_id: int) -> None:
        post.is_deleted = True
        post.updated_by = deleter_id
        self.db.flush()
