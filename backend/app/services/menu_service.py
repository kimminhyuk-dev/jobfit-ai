"""관리자 동적 메뉴 비즈니스 로직."""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_log import (
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_DELETE,
    AUDIT_ACTION_UPDATE,
)
from app.models.menu import Menu
from app.repositories.audit_log_repository import record_audit
from app.repositories.menu_repository import MenuRepository
from app.schemas.menu import MenuCreate, MenuResponse, MenuTreeResponse, MenuUpdate


class MenuNotFoundError(Exception):
    """메뉴를 찾을 수 없음."""


class MenuInvalidParentError(Exception):
    """상위 메뉴 설정이 올바르지 않음."""


class MenuInvalidRequestError(Exception):
    """메뉴 요청이 올바르지 않음."""


class MenuService:
    """관리자 메뉴 관리 서비스."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MenuRepository(db)

    def list_menus(self) -> list[MenuResponse]:
        """관리용 메뉴 목록을 조회한다."""
        return [self._response(menu) for menu in self.repository.list_all()]

    def get_tree_for_user(self, permission_codes: set[str]) -> list[MenuTreeResponse]:
        """현재 사용자의 권한 기준으로 메뉴 트리를 조회한다."""
        menus = [
            menu
            for menu in self.repository.list_all()
            if menu.use_yn and self._is_allowed(menu, permission_codes)
        ]
        return self._build_tree(menus)

    def get_management_tree(self) -> list[MenuTreeResponse]:
        """관리 화면용 전체 메뉴 트리를 조회한다."""
        return self._build_tree(self.repository.list_all())

    def create_menu(
        self,
        payload: MenuCreate,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> MenuResponse:
        """메뉴를 생성한다."""
        if payload.parent_id is not None:
            self._get_menu_or_raise(payload.parent_id)
        try:
            menu = self.repository.create(payload)
        except IntegrityError as exc:
            self.db.rollback()
            raise MenuInvalidRequestError from exc
        record_audit(
            self.db,
            table_name="menus",
            record_id=menu.id,
            action=AUDIT_ACTION_CREATE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            after_data=self._data(menu),
            summary="관리자 메뉴 생성",
        )
        self.db.commit()
        self.db.refresh(menu)
        return self._response(menu)

    def update_menu(
        self,
        menu_id: int,
        payload: MenuUpdate,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> MenuResponse:
        """메뉴를 수정한다."""
        menu = self._get_menu_or_raise(menu_id)
        if "parent_id" in payload.model_fields_set:
            self._validate_parent(menu_id, payload.parent_id)

        before_data = self._data(menu)
        try:
            menu = self.repository.update(menu, payload)
        except IntegrityError as exc:
            self.db.rollback()
            raise MenuInvalidRequestError from exc
        record_audit(
            self.db,
            table_name="menus",
            record_id=menu.id,
            action=AUDIT_ACTION_UPDATE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            before_data=before_data,
            after_data=self._data(menu),
            summary="관리자 메뉴 수정",
        )
        self.db.commit()
        self.db.refresh(menu)
        return self._response(menu)

    def delete_menu(
        self,
        menu_id: int,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> None:
        """메뉴를 삭제한다."""
        menu = self._get_menu_or_raise(menu_id)
        before_data = self._data(menu)
        self.repository.soft_delete(menu)
        record_audit(
            self.db,
            table_name="menus",
            record_id=menu.id,
            action=AUDIT_ACTION_DELETE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            before_data=before_data,
            after_data=self._data(menu),
            summary="관리자 메뉴 삭제",
        )
        self.db.commit()

    def _validate_parent(self, menu_id: int, parent_id: int | None) -> None:
        if parent_id is None:
            return
        if parent_id == menu_id:
            raise MenuInvalidParentError

        menus = {menu.id: menu for menu in self.repository.list_all()}
        if parent_id not in menus:
            raise MenuNotFoundError

        cursor = menus[parent_id]
        while cursor.parent_id is not None:
            if cursor.parent_id == menu_id:
                raise MenuInvalidParentError
            cursor = menus.get(cursor.parent_id)
            if cursor is None:
                break

    def _get_menu_or_raise(self, menu_id: int) -> Menu:
        menu = self.repository.get_by_id(menu_id)
        if menu is None:
            raise MenuNotFoundError
        return menu

    @staticmethod
    def _is_allowed(menu: Menu, permission_codes: set[str]) -> bool:
        if menu.required_permission is None:
            return True
        return menu.required_permission in permission_codes

    @classmethod
    def _build_tree(cls, menus: list[Menu]) -> list[MenuTreeResponse]:
        responses = {menu.id: cls._tree_response(menu) for menu in menus}
        roots: list[MenuTreeResponse] = []
        for menu in menus:
            node = responses[menu.id]
            if menu.parent_id is not None and menu.parent_id in responses:
                responses[menu.parent_id].children.append(node)
            else:
                roots.append(node)
        cls._sort_tree(roots)
        return roots

    @classmethod
    def _sort_tree(cls, nodes: list[MenuTreeResponse]) -> None:
        nodes.sort(key=lambda node: (node.sort_order, node.id))
        for node in nodes:
            cls._sort_tree(node.children)

    @staticmethod
    def _data(menu: Menu) -> dict[str, Any]:
        return {
            "id": menu.id,
            "parent_id": menu.parent_id,
            "menu_name": menu.menu_name,
            "menu_url": menu.menu_url,
            "icon": menu.icon,
            "sort_order": menu.sort_order,
            "use_yn": menu.use_yn,
            "required_permission": menu.required_permission,
        }

    @classmethod
    def _response(cls, menu: Menu) -> MenuResponse:
        return MenuResponse(
            **cls._data(menu),
            created_at=menu.created_at,
            updated_at=menu.updated_at,
            reg_user_id=menu.reg_user_id,
            reg_ip=menu.reg_ip,
            reg_dt=menu.reg_dt,
            mod_user_id=menu.mod_user_id,
            mod_ip=menu.mod_ip,
            mod_dt=menu.mod_dt,
        )

    @classmethod
    def _tree_response(cls, menu: Menu) -> MenuTreeResponse:
        return MenuTreeResponse(
            **cls._response(menu).model_dump(),
            children=[],
        )
