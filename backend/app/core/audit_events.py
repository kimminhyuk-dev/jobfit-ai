"""감사 칼럼과 핵심 감사 로그를 자동으로 남기는 SQLAlchemy 이벤트."""

from __future__ import annotations

from sqlalchemy import Connection, event, select
from sqlalchemy.orm import Mapper

from app.core.audit_context import apply_reg_mod_columns, get_audit_context
from app.models.audit_log import AUDIT_ACTION_CREATE, AUDIT_ACTION_DELETE
from app.models.rbac import Role, UserRole
from app.repositories.audit_log_repository import record_audit_with_connection

_registered = False


def register_audit_events() -> None:
    """감사 이벤트를 한 번만 등록한다."""
    global _registered
    if _registered:
        return

    event.listen(Mapper, "before_insert", _before_insert)
    event.listen(Mapper, "before_update", _before_update)
    event.listen(UserRole, "after_insert", _after_user_role_insert)
    event.listen(UserRole, "after_delete", _after_user_role_delete)
    _registered = True


def _before_insert(_mapper, _connection: Connection, target: object) -> None:
    apply_reg_mod_columns(target, is_insert=True)


def _before_update(_mapper, _connection: Connection, target: object) -> None:
    apply_reg_mod_columns(target, is_insert=False)


def _after_user_role_insert(_mapper, connection: Connection, target: UserRole) -> None:
    context = get_audit_context()
    data = _user_role_data(connection, target)
    record_audit_with_connection(
        connection,
        table_name="user_roles",
        record_id=target.user_role_id,
        action=AUDIT_ACTION_CREATE,
        actor_user_id=context.user_id,
        actor_ip=context.ip,
        before_data=None,
        after_data=data,
        summary="사용자 역할 부여",
    )


def _after_user_role_delete(_mapper, connection: Connection, target: UserRole) -> None:
    context = get_audit_context()
    data = _user_role_data(connection, target)
    record_audit_with_connection(
        connection,
        table_name="user_roles",
        record_id=target.user_role_id,
        action=AUDIT_ACTION_DELETE,
        actor_user_id=context.user_id,
        actor_ip=context.ip,
        before_data=data,
        after_data=None,
        summary="사용자 역할 회수",
    )


def _user_role_data(connection: Connection, target: UserRole) -> dict[str, int | str | None]:
    role_code = connection.execute(
        select(Role.code).where(Role.role_id == target.role_id)
    ).scalar_one_or_none()
    return {
        "user_role_id": target.user_role_id,
        "user_id": target.user_id,
        "role_id": target.role_id,
        "role_code": role_code,
    }
