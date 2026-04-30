from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    total_users: int
    active_categories: int
    total_posts: int
    today_signups: int
    total_jobs: int
