"""
FastAPI 앱 진입점
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import (
    admin_jobs_router,
    admin_stats_router,
    admin_users_router,
    auth_router,
    categories_router,
    jobs_router,
    posts_router,
    resumes_router,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers


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

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(posts_router)
app.include_router(admin_jobs_router)
app.include_router(admin_stats_router)
app.include_router(admin_users_router)
app.include_router(jobs_router)
app.include_router(resumes_router)


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
