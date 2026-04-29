"""
FastAPI 앱 진입점
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import auth_router, categories_router, posts_router
from app.core.config import settings
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers


app = FastAPI(
    title=settings.app_name,
    description="AI 기반 이력서-채용공고 매칭 플랫폼",
    version="0.1.0",
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(posts_router)


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
