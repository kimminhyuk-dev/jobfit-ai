"""
애플리케이션 설정
.env 파일의 환경변수를 타입 안전하게 읽어오는 모듈
"""

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

    # Auth Cookie
    refresh_token_cookie_name: str = "refresh_token"
    refresh_token_cookie_secure: bool = False
    refresh_token_cookie_samesite: str = "lax"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]


# 전역 싱글톤
settings = Settings()
