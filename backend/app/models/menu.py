"""관리자 동적 메뉴 모델."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, RegModAuditMixin, SoftDeleteMixin


class Menu(Base, AuditMixin, RegModAuditMixin, SoftDeleteMixin):
    """관리자 사이드바 메뉴 트리."""

    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="메뉴 PK",
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("menus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="상위 메뉴 ID",
    )
    menu_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="메뉴명",
    )
    menu_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="메뉴 URL",
    )
    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="아이콘 이름",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="정렬 순서",
    )
    use_yn: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="사용 여부",
    )
    required_permission: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("permissions.code", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="노출 필요 권한 코드",
    )
