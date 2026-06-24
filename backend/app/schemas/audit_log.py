"""감사 로그 요청·응답 스키마."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """감사 로그 한 건."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    table_name: str
    record_id: str
    action: str
    actor_user_id: int | None
    actor_ip: str | None
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    summary: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """감사 로그 페이지 응답."""

    items: list[AuditLogResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
