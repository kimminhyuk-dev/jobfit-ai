"""
Alembic 마이그레이션 실행 환경 설정

실행 흐름:
1. alembic.ini 읽기
2. 우리 프로젝트 설정(settings) 로드 → .env 값 포함
3. 우리 Base(모델 정의의 부모) 로드
4. DB URL과 메타데이터를 alembic에 넘김
5. alembic이 마이그레이션 실행
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ─────────────────────────────────────────────
# 1) 프로젝트 루트를 Python path에 추가
#    alembic/env.py에서 app/... 를 import 하려면 필요
# ─────────────────────────────────────────────
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────
# 2) 우리 프로젝트 import
# ─────────────────────────────────────────────
from app.core.config import settings
from app.core.database import Base

# 모델 import (Alembic이 감지하려면 반드시 필요)
from app.models import user  # noqa: F401
from app.models import category  # noqa: F401
from app.models import post  # noqa: F401
from app.models import job_posting  # noqa: F401
from app.models import batch_job_run  # noqa: F401
from app.models import common_code  # noqa: F401
from app.models import job_source  # noqa: F401
from app.models import refresh_token  # noqa: F401
from app.models import resume  # noqa: F401
from app.models import resume_chunk  # noqa: F401
from app.models import resume_project  # noqa: F401
from app.models import resume_cover_letter_section  # noqa: F401
from app.models import resume_interview  # noqa: F401
from app.models import mock_interview  # noqa: F401
from app.models import company  # noqa: F401
from app.models import application  # noqa: F401
from app.models import email_verification  # noqa: F401
from app.models import team  # noqa: F401
from app.models import rbac  # noqa: F401
from app.models import admin_leave  # noqa: F401
from app.models import audit_log  # noqa: F401
from app.models import menu  # noqa: F401

# ─────────────────────────────────────────────
# 3) alembic.ini 읽기
# ─────────────────────────────────────────────
config = context.config

# .env의 DATABASE_URL을 alembic 설정에 주입
config.set_main_option("sqlalchemy.url", settings.database_url)

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─────────────────────────────────────────────
# 4) 마이그레이션이 추적할 메타데이터
#    Base를 상속한 모든 모델의 테이블이 자동 감지됨
# ─────────────────────────────────────────────
target_metadata = Base.metadata


# ─────────────────────────────────────────────
# 5) 오프라인 모드: SQL 파일만 생성
# ─────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ─────────────────────────────────────────────
# 6) 온라인 모드: 실제 DB에 연결해서 실행 (우리가 쓸 모드)
# ─────────────────────────────────────────────
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 컬럼 타입 변경 감지
        )
        with context.begin_transaction():
            context.run_migrations()


# ─────────────────────────────────────────────
# 7) 모드 분기
# ─────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
