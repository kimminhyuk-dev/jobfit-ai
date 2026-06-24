from app.api.admin_audit_logs import router as admin_audit_logs_router
from app.api.admin_common_codes import router as admin_common_codes_router
from app.api.admin_leave import router as admin_leave_router
from app.api.admin_menus import router as admin_menus_router
from app.api.admin_jobs import router as admin_jobs_router
from app.api.admin_stats import router as admin_stats_router
from app.api.admin_users import router as admin_users_router
from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.categories import admin_router as admin_categories_router
from app.api.categories import router as categories_router
from app.api.company import router as company_router
from app.api.jobs import router as jobs_router
from app.api.posts import router as posts_router
from app.api.resumes import router as resumes_router

__all__ = [
    "admin_jobs_router",
    "admin_audit_logs_router",
    "admin_common_codes_router",
    "admin_leave_router",
    "admin_menus_router",
    "admin_stats_router",
    "admin_users_router",
    "admin_categories_router",
    "applications_router",
    "auth_router",
    "categories_router",
    "company_router",
    "jobs_router",
    "posts_router",
    "resumes_router",
]
