"""관리자 메뉴 DB 접근 계층."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate


class MenuRepository:
    """관리자 메뉴 저장소."""

    def __init__(self, db: Session):
        self.db = db

    def list_all(self, *, include_deleted: bool = False) -> list[Menu]:
        """관리자 메뉴 전체 목록을 조회한다."""
        stmt = select(Menu)
        if not include_deleted:
            stmt = stmt.where(Menu.is_deleted.is_(False))
        stmt = stmt.order_by(Menu.sort_order.asc(), Menu.id.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, menu_id: int, *, include_deleted: bool = False) -> Menu | None:
        """메뉴 ID로 메뉴를 조회한다."""
        stmt = select(Menu).where(Menu.id == menu_id)
        if not include_deleted:
            stmt = stmt.where(Menu.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, payload: MenuCreate) -> Menu:
        """관리자 메뉴를 생성한다."""
        menu = Menu(
            parent_id=payload.parent_id,
            menu_name=payload.menu_name,
            menu_url=payload.menu_url,
            icon=payload.icon,
            sort_order=payload.sort_order,
            use_yn=payload.use_yn,
            required_permission=payload.required_permission,
        )
        self.db.add(menu)
        self.db.flush()
        return menu

    def update(self, menu: Menu, payload: MenuUpdate) -> Menu:
        """관리자 메뉴를 수정한다."""
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(menu, field, value)
        self.db.flush()
        return menu

    def soft_delete(self, menu: Menu) -> Menu:
        """관리자 메뉴를 비활성 삭제 처리한다."""
        menu.use_yn = False
        menu.is_deleted = True
        self.db.flush()
        return menu
