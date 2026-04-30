from sqlalchemy.orm import Session

from app.repositories.category_repository import CategoryRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_stats import AdminStatsResponse


class AdminStatsService:
    def __init__(self, db: Session):
        self._user_repo = UserRepository(db)
        self._category_repo = CategoryRepository(db)
        self._post_repo = PostRepository(db)
        self._job_repo = JobPostingRepository(db)

    def get_stats(self) -> AdminStatsResponse:
        return AdminStatsResponse(
            total_users=self._user_repo.count_total(),
            active_categories=self._category_repo.count_active(),
            total_posts=self._post_repo.count_total(),
            today_signups=self._user_repo.count_today(),
            total_jobs=self._job_repo.count_all(),
        )
