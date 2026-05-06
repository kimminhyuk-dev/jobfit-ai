"""
애플리케이션 설정
.env 파일의 환경변수를 타입 안전하게 읽어오는 모듈
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "jobfit-ai"
    app_env: str = "development"
    app_port: int = 8000

    # DB
    database_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 14

    # Auth Cookie — Access Token
    access_token_cookie_name: str = "access_token"
    access_token_cookie_secure: bool = False
    access_token_cookie_samesite: str = "lax"

    # Auth Cookie — Refresh Token
    refresh_token_cookie_name: str = "refresh_token"
    refresh_token_cookie_secure: bool = False
    refresh_token_cookie_samesite: str = "lax"

    # Work24 OpenAPI
    work24_base_url: str = "https://www.work24.go.kr"
    work24_job_api_key: str = ""
    work24_department_api_key: str = ""
    work24_duty_api_key: str = ""
    work24_common_code_api_key: str = ""
    work24_occupation_api_key: str = ""

    # ALIO / 공공기관 채용정보 API
    alio_base_url: str = "https://opendata.alio.go.kr"
    alio_api_key: str = ""
    # Deprecated: endpoint paths are managed in alio_client.py.
    # These fields are kept only so old local .env files do not break startup.
    alio_recruit_list_url: str | None = Field(default=None)
    alio_recruit_detail_url: str | None = Field(default=None)

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # Resume upload
    resume_upload_dir: str = "data/resumes"
    resume_max_upload_mb: int = 10

    # Google Gemini API (Free Tier 사용 가능)
    gemini_api_key: str = ""


# 전역 싱글톤
settings = Settings()
