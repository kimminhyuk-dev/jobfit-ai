"""관리자 사용자 역할 부여/회수 스키마."""

from pydantic import BaseModel, ConfigDict, Field


class RolePermissionItem(BaseModel):
    """역할이 보유한 권한 단건."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str


class AssignableRole(BaseModel):
    """부여 가능한 역할과 그 역할의 권한 목록."""

    code: str
    name: str
    description: str | None = None
    permissions: list[RolePermissionItem] = Field(default_factory=list)


class UserRolesResponse(BaseModel):
    """사용자가 보유한 역할과 부여 가능한 전체 역할 정보."""

    user_id: int
    name: str
    email: str
    assigned_role_codes: list[str]
    super_admin_count: int
    available_roles: list[AssignableRole]


class RoleAssignRequest(BaseModel):
    """역할 부여 요청 본문."""

    role_code: str = Field(min_length=1, max_length=50)
