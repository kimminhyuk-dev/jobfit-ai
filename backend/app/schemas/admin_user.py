from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.resume import ResumeListItem
from app.schemas.user import UserResponse


class AdminCompanySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    user_id: int
    company_name: str | None
    business_number: str | None
    representative_name: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminUserListItem(UserResponse):
    company: AdminCompanySummary | None = None


class AdminUserDetail(BaseModel):
    user: AdminUserListItem
    resumes: list[ResumeListItem]
