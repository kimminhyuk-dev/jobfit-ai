"""감사 칼럼 자동 입력에 쓰는 요청 컨텍스트."""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Request


@dataclass(frozen=True)
class AuditContext:
    """현재 요청의 사용자와 접속 IP."""

    user_id: int | None = None
    ip: str | None = None


_audit_context: ContextVar[AuditContext] = ContextVar(
    "audit_context",
    default=AuditContext(),
)


def get_client_ip_from_request(request: Request) -> str | None:
    """프록시 헤더를 우선해 요청 IP를 구한다."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or None
    if request.client:
        return request.client.host
    return None


def get_audit_context() -> AuditContext:
    """현재 감사 컨텍스트를 반환한다."""
    return _audit_context.get()


def set_audit_context(
    *,
    user_id: int | None = None,
    ip: str | None = None,
) -> Token[AuditContext]:
    """현재 요청의 감사 컨텍스트를 갱신한다."""
    current = _audit_context.get()
    return _audit_context.set(
        AuditContext(
            user_id=current.user_id if user_id is None else user_id,
            ip=current.ip if ip is None else ip,
        )
    )


def reset_audit_context(token: Token[AuditContext]) -> None:
    """요청 처리가 끝난 뒤 이전 컨텍스트로 되돌린다."""
    _audit_context.reset(token)


def apply_reg_mod_columns(target: object, *, is_insert: bool) -> None:
    """대상 모델에 reg/mod 감사 칼럼이 있으면 현재 컨텍스트로 채운다."""
    if not hasattr(target, "mod_user_id"):
        return

    context = get_audit_context()
    now = datetime.now(timezone.utc)

    if is_insert:
        if getattr(target, "reg_user_id", None) is None:
            setattr(target, "reg_user_id", context.user_id)
        if getattr(target, "reg_ip", None) is None:
            setattr(target, "reg_ip", context.ip)
        if getattr(target, "reg_dt", None) is None:
            setattr(target, "reg_dt", now)

    if getattr(target, "mod_user_id", None) is None or not is_insert:
        setattr(target, "mod_user_id", context.user_id)
    if getattr(target, "mod_ip", None) is None or not is_insert:
        setattr(target, "mod_ip", context.ip)
    setattr(target, "mod_dt", now)
