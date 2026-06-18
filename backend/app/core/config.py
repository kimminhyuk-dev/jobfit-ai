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

    # OpenAI API (이력서 면접 연습 기능 — 저비용 모델 사용)
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    openai_max_output_tokens: int = 6000
    # 추론 모델(gpt-5 계열)의 reasoning 강도. 낮을수록 응답이 빠르다.
    # 허용: "minimal" | "low" | "medium" | "high"
    openai_reasoning_effort: str = "low"

    # SMTP / 메일 발송 (Spring JobFolio의 spring.mail.* 를 Python .env 스타일로 이식)
    # 환경변수 매칭은 대소문자 무관 → .env의 SMTP_HOST 가 smtp_host 로 매핑된다.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_auth: bool = True
    smtp_use_tls: bool = True
    smtp_require_tls: bool = True
    # Spring은 타임아웃을 밀리초로 받는다. email_service에서 초 단위로 환산해 사용한다.
    smtp_connection_timeout_ms: int = 5000
    smtp_timeout_ms: int = 5000
    smtp_write_timeout_ms: int = 5000
    smtp_ssl_trust: str | None = "smtp.gmail.com"

    # Google Maps Static API (면접 메일에 첨부할 지도 이미지 생성용)
    # 키는 메일 본문에 직접 노출하지 않고, 서버에서만 사용해 이미지 바이트를 받아온다.
    google_maps_api_key: str | None = None
    google_maps_static_base_url: str = "https://maps.googleapis.com/maps/api/staticmap"


# 전역 싱글톤
settings = Settings()
