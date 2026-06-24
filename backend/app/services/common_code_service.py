"""공통코드 관리 비즈니스 로직."""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.audit_log import (
    AUDIT_ACTION_CREATE,
    AUDIT_ACTION_DELETE,
    AUDIT_ACTION_UPDATE,
)
from app.models.common_code import CommonCode, CommonCodeGroup
from app.repositories.audit_log_repository import record_audit
from app.repositories.common_code_repository import CommonCodeRepository
from app.schemas.common_code import (
    CommonCodeGroupCreate,
    CommonCodeGroupResponse,
    CommonCodeGroupUpdate,
    CommonCodeItemCreate,
    CommonCodeItemResponse,
    CommonCodeItemUpdate,
)


class CommonCodeNotFoundError(Exception):
    """공통코드를 찾을 수 없음."""


class CommonCodeDuplicateError(Exception):
    """공통코드가 중복됨."""


class CommonCodeGroupHasItemsError(Exception):
    """상세 코드가 있어 그룹을 삭제할 수 없음."""


class CommonCodeService:
    """공통코드 관리 서비스."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = CommonCodeRepository(db)

    def list_groups(self) -> list[CommonCodeGroupResponse]:
        """공통코드 그룹 목록을 조회한다."""
        return [self._group_response(group) for group in self.repository.list_groups()]

    def create_group(
        self,
        payload: CommonCodeGroupCreate,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> CommonCodeGroupResponse:
        """공통코드 그룹을 생성한다."""
        try:
            group = self.repository.create_group(payload)
        except IntegrityError as exc:
            self.db.rollback()
            raise CommonCodeDuplicateError from exc
        record_audit(
            self.db,
            table_name="common_code_groups",
            record_id=group.code_group,
            action=AUDIT_ACTION_CREATE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            after_data=self._group_data(group),
            summary="공통코드 그룹 생성",
        )
        self.db.commit()
        self.db.refresh(group)
        return self._group_response(group)

    def update_group(
        self,
        group_code: str,
        payload: CommonCodeGroupUpdate,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> CommonCodeGroupResponse:
        """공통코드 그룹을 수정한다."""
        group = self._get_group_or_raise(group_code)
        before_data = self._group_data(group)
        try:
            group = self.repository.update_group(group, payload)
        except IntegrityError as exc:
            self.db.rollback()
            raise CommonCodeDuplicateError from exc
        record_audit(
            self.db,
            table_name="common_code_groups",
            record_id=group.code_group,
            action=AUDIT_ACTION_UPDATE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            before_data=before_data,
            after_data=self._group_data(group),
            summary="공통코드 그룹 수정",
        )
        self.db.commit()
        self.db.refresh(group)
        return self._group_response(group)

    def delete_group(
        self,
        group_code: str,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> None:
        """공통코드 그룹을 삭제한다."""
        group = self._get_group_or_raise(group_code)
        if self.repository.list_items(group_code):
            raise CommonCodeGroupHasItemsError
        before_data = self._group_data(group)
        self.repository.soft_delete_group(group)
        record_audit(
            self.db,
            table_name="common_code_groups",
            record_id=group.code_group,
            action=AUDIT_ACTION_DELETE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            before_data=before_data,
            after_data=self._group_data(group),
            summary="공통코드 그룹 삭제",
        )
        self.db.commit()

    def list_items(self, group_code: str) -> list[CommonCodeItemResponse]:
        """그룹별 상세 코드 목록을 조회한다."""
        self._get_group_or_raise(group_code)
        return [self._item_response(item) for item in self.repository.list_items(group_code)]

    def create_item(
        self,
        group_code: str,
        payload: CommonCodeItemCreate,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> CommonCodeItemResponse:
        """상세 코드를 생성한다."""
        self._get_group_or_raise(group_code)
        try:
            item = self.repository.create_item(group_code, payload)
        except IntegrityError as exc:
            self.db.rollback()
            raise CommonCodeDuplicateError from exc
        record_audit(
            self.db,
            table_name="common_codes",
            record_id=f"{item.code_group}:{item.code}",
            action=AUDIT_ACTION_CREATE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            after_data=self._item_data(item),
            summary="공통코드 상세 생성",
        )
        self.db.commit()
        self.db.refresh(item)
        return self._item_response(item)

    def update_item(
        self,
        group_code: str,
        code: str,
        payload: CommonCodeItemUpdate,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> CommonCodeItemResponse:
        """상세 코드를 수정한다."""
        item = self._get_item_or_raise(group_code, code)
        before_data = self._item_data(item)
        item = self.repository.update_item(item, payload)
        record_audit(
            self.db,
            table_name="common_codes",
            record_id=f"{item.code_group}:{item.code}",
            action=AUDIT_ACTION_UPDATE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            before_data=before_data,
            after_data=self._item_data(item),
            summary="공통코드 상세 수정",
        )
        self.db.commit()
        self.db.refresh(item)
        return self._item_response(item)

    def delete_item(
        self,
        group_code: str,
        code: str,
        *,
        actor_id: int,
        request_ip: str | None,
    ) -> None:
        """상세 코드를 삭제한다."""
        item = self._get_item_or_raise(group_code, code)
        before_data = self._item_data(item)
        self.repository.soft_delete_item(item)
        record_audit(
            self.db,
            table_name="common_codes",
            record_id=f"{item.code_group}:{item.code}",
            action=AUDIT_ACTION_DELETE,
            actor_user_id=actor_id,
            actor_ip=request_ip,
            before_data=before_data,
            after_data=self._item_data(item),
            summary="공통코드 상세 삭제",
        )
        self.db.commit()

    def _get_group_or_raise(self, group_code: str) -> CommonCodeGroup:
        group = self.repository.get_group(group_code)
        if group is None:
            raise CommonCodeNotFoundError
        return group

    def _get_item_or_raise(self, group_code: str, code: str) -> CommonCode:
        item = self.repository.get_item(group_code, code)
        if item is None:
            raise CommonCodeNotFoundError
        return item

    @staticmethod
    def _group_data(group: CommonCodeGroup) -> dict[str, Any]:
        return {
            "id": group.group_id,
            "group_code": group.code_group,
            "group_name": group.code_group_name,
            "description": group.description,
            "sort_order": group.sort_order,
            "use_yn": group.use_yn,
            "category_code": group.category_code,
        }

    @staticmethod
    def _item_data(item: CommonCode) -> dict[str, Any]:
        return {
            "id": item.code_id,
            "group_code": item.code_group,
            "code": item.code,
            "code_name": item.code_name,
            "sort_order": item.sort_order,
            "use_yn": item.use_yn,
            "attr1": item.attr1,
            "attr2": item.attr2,
        }

    @classmethod
    def _group_response(cls, group: CommonCodeGroup) -> CommonCodeGroupResponse:
        return CommonCodeGroupResponse(
            **cls._group_data(group),
            created_at=group.created_at,
            updated_at=group.updated_at,
            reg_user_id=group.reg_user_id,
            reg_ip=group.reg_ip,
            reg_dt=group.reg_dt,
            mod_user_id=group.mod_user_id,
            mod_ip=group.mod_ip,
            mod_dt=group.mod_dt,
        )

    @classmethod
    def _item_response(cls, item: CommonCode) -> CommonCodeItemResponse:
        return CommonCodeItemResponse(
            **cls._item_data(item),
            created_at=item.created_at,
            updated_at=item.updated_at,
            reg_user_id=item.reg_user_id,
            reg_ip=item.reg_ip,
            reg_dt=item.reg_dt,
            mod_user_id=item.mod_user_id,
            mod_ip=item.mod_ip,
            mod_dt=item.mod_dt,
        )
