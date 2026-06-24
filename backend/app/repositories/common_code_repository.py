"""공통코드 DB 접근 계층."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.common_code import CommonCode, CommonCodeGroup
from app.schemas.common_code import (
    CommonCodeGroupCreate,
    CommonCodeGroupUpdate,
    CommonCodeItemCreate,
    CommonCodeItemUpdate,
)


class CommonCodeRepository:
    """공통코드 그룹과 상세 코드 저장소."""

    def __init__(self, db: Session):
        self.db = db

    def list_groups(self, *, include_deleted: bool = False) -> list[CommonCodeGroup]:
        """공통코드 그룹 목록을 조회한다."""
        stmt = select(CommonCodeGroup)
        if not include_deleted:
            stmt = stmt.where(CommonCodeGroup.is_deleted.is_(False))
        stmt = stmt.order_by(CommonCodeGroup.sort_order.asc(), CommonCodeGroup.code_group.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_group(self, group_code: str, *, include_deleted: bool = False) -> CommonCodeGroup | None:
        """그룹 코드로 공통코드 그룹을 조회한다."""
        stmt = select(CommonCodeGroup).where(CommonCodeGroup.code_group == group_code)
        if not include_deleted:
            stmt = stmt.where(CommonCodeGroup.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def create_group(self, payload: CommonCodeGroupCreate) -> CommonCodeGroup:
        """공통코드 그룹을 생성한다."""
        group = CommonCodeGroup(
            category_code=payload.category_code,
            code_group=payload.group_code,
            code_group_name=payload.group_name,
            description=payload.description,
            sort_order=payload.sort_order,
            use_yn=payload.use_yn,
            is_active=payload.use_yn,
        )
        self.db.add(group)
        self.db.flush()
        return group

    def update_group(
        self,
        group: CommonCodeGroup,
        payload: CommonCodeGroupUpdate,
    ) -> CommonCodeGroup:
        """공통코드 그룹을 수정한다."""
        data = payload.model_dump(exclude_unset=True)
        if "group_name" in data:
            group.code_group_name = data["group_name"]
        if "description" in data:
            group.description = data["description"]
        if "sort_order" in data:
            group.sort_order = data["sort_order"]
        if "use_yn" in data:
            group.use_yn = data["use_yn"]
            group.is_active = data["use_yn"]
        self.db.flush()
        return group

    def soft_delete_group(self, group: CommonCodeGroup) -> CommonCodeGroup:
        """공통코드 그룹을 비활성 삭제 처리한다."""
        group.use_yn = False
        group.is_active = False
        group.is_deleted = True
        self.db.flush()
        return group

    def list_items(
        self,
        group_code: str,
        *,
        include_deleted: bool = False,
    ) -> list[CommonCode]:
        """그룹별 상세 코드 목록을 조회한다."""
        stmt = select(CommonCode).where(CommonCode.code_group == group_code)
        if not include_deleted:
            stmt = stmt.where(CommonCode.is_deleted.is_(False))
        stmt = stmt.order_by(CommonCode.sort_order.asc(), CommonCode.code.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_item(
        self,
        group_code: str,
        code: str,
        *,
        include_deleted: bool = False,
    ) -> CommonCode | None:
        """그룹 코드와 상세 코드로 상세 코드를 조회한다."""
        stmt = (
            select(CommonCode)
            .where(CommonCode.code_group == group_code)
            .where(CommonCode.code == code)
        )
        if not include_deleted:
            stmt = stmt.where(CommonCode.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def create_item(
        self,
        group_code: str,
        payload: CommonCodeItemCreate,
    ) -> CommonCode:
        """상세 코드를 생성한다."""
        item = CommonCode(
            code_group=group_code,
            code=payload.code,
            code_name=payload.code_name,
            sort_order=payload.sort_order,
            use_yn=payload.use_yn,
            is_active=payload.use_yn,
            attr1=payload.attr1,
            attr2=payload.attr2,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def update_item(
        self,
        item: CommonCode,
        payload: CommonCodeItemUpdate,
    ) -> CommonCode:
        """상세 코드를 수정한다."""
        data = payload.model_dump(exclude_unset=True)
        if "code_name" in data:
            item.code_name = data["code_name"]
        if "sort_order" in data:
            item.sort_order = data["sort_order"]
        if "use_yn" in data:
            item.use_yn = data["use_yn"]
            item.is_active = data["use_yn"]
        if "attr1" in data:
            item.attr1 = data["attr1"]
        if "attr2" in data:
            item.attr2 = data["attr2"]
        self.db.flush()
        return item

    def soft_delete_item(self, item: CommonCode) -> CommonCode:
        """상세 코드를 비활성 삭제 처리한다."""
        item.use_yn = False
        item.is_active = False
        item.is_deleted = True
        self.db.flush()
        return item
