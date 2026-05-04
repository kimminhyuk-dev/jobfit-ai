from app.api.admin_jobs import router as admin_jobs_router
from app.api.admin_stats import router as admin_stats_router
from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.jobs import router as jobs_router
from app.api.posts import router as posts_router
from app.api.resumes import router as resumes_router

__all__ = [
    "admin_jobs_router",
    "admin_stats_router",
    "auth_router",
    "categories_router",
    "jobs_router",
    "posts_router",
    "resumes_router",
]
