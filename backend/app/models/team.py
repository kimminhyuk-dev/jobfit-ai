"""
Team(조직/팀) 모델

휴가 결재선 계산의 기준 단위.
- 팀원(MEMBER)의 1차 승인자 = 같은 팀의 LEAD
- 팀장(LEAD)의 승인자 = SUPER_ADMIN

users.team_id / users.team_role 컬럼으로 사용자와 연결한다(team.py가 아닌 user.py에 정의).
"""

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin

# 팀 내 역할 (users.team_role 값)
TEAM_ROLE_LEAD = "LEAD"
TEAM_ROLE_MEMBER = "MEMBER"

TEAM_ROLE_VALUES = {TEAM_ROLE_LEAD, TEAM_ROLE_MEMBER}


class Team(Base, AuditMixin, SoftDeleteMixin):
    """조직(팀) 테이블."""

    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="팀 PK",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="팀 이름",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="팀 설명",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="활성 여부",
    )

    def __repr__(self) -> str:
        return f"<Team(team_id={self.team_id}, name={self.name})>"
