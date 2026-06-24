"""
FastAPI 앱 진입점
"""

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import (
    admin_audit_logs_router,
    admin_common_codes_router,
    admin_jobs_router,
    admin_leave_router,
    admin_menus_router,
    admin_stats_router,
    admin_users_router,
    admin_categories_router,
    applications_router,
    auth_router,
    categories_router,
    company_router,
    jobs_router,
    posts_router,
    resumes_router,
)
from app.core.audit_context import (
    get_client_ip_from_request,
    reset_audit_context,
    set_audit_context,
)
from app.core.audit_events import register_audit_events
from app.core.config import settings
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import decode_token


app = FastAPI(
    title=settings.app_name,
    description="AI 기반 이력서-채용공고 매칭 플랫폼",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
register_audit_events()


@app.middleware("http")
async def audit_context_middleware(request: Request, call_next):
    """요청 단위 감사 컨텍스트를 준비한다."""
    token_value = request.cookies.get(settings.access_token_cookie_name)
    user_id: int | None = None
    if token_value:
        try:
            payload = decode_token(token_value, expected_type="access")
            user_id = int(payload["sub"])
        except (KeyError, TypeError, ValueError):
            user_id = None

    context_token = set_audit_context(
        user_id=user_id,
        ip=get_client_ip_from_request(request),
    )
    try:
        return await call_next(request)
    finally:
        reset_audit_context(context_token)


app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(posts_router)
app.include_router(admin_audit_logs_router)
app.include_router(admin_common_codes_router)
app.include_router(admin_jobs_router)
app.include_router(admin_leave_router)
app.include_router(admin_menus_router)
app.include_router(admin_stats_router)
app.include_router(admin_users_router)
app.include_router(admin_categories_router)
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(applications_router)
app.include_router(company_router)


@app.get("/")
def root():
    """루트 — 서비스 기본 정보"""
    return {
        "app": settings.app_name,
        "env": settings.app_env,
        "status": "ok",
    }


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@app.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """헬스 체크 — DB 연결 여부"""
    result = db.execute(text("SELECT 1")).scalar()
    return {"status": "healthy" if result == 1 else "unhealthy", "db": "connected"}
