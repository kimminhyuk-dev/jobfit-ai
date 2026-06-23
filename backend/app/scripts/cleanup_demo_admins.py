"""데모 관리자 계정을 현업에 가까운 소규모 조직으로 정리한다(멱등).

정책:
- 목표 조직(seed_demo_accounts.ADMIN_ORG)에 해당하는 데모 관리자만 남긴다.
- 그 외 데모 관리자(adminNNN@demo.jobfit.local)는 하드 삭제한다.
  user_roles / refresh_tokens 등은 FK ON DELETE CASCADE로 함께 정리된다.
- 비데모/실관리자(예: NULL 등급 test 계정)와 USER/COMPANY 데모 계정은 건드리지 않는다.
- 남긴 관리자에는 목표 역할/팀/등급을 정규화 적용한다(OPS_ADMIN 승격 포함).
- 여러 번 실행해도 동일 상태로 수렴한다(멱등).

안전장치:
- 기본은 dry-run(미리보기)이며, 실제 삭제는 --apply 가 있어야 수행한다.
- 삭제 대상은 항상 role='ADMIN' AND email LIKE '%@demo.jobfit.local' 로 한정한다.

Usage:
    python -m app.scripts.cleanup_demo_admins            # 미리보기(dry-run)
    python -m app.scripts.cleanup_demo_admins --apply    # 실제 적용
"""

from __future__ import annotations

import argparse

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.scripts.seed_demo_accounts import (
    ADMIN_ORG_EMAILS,
    EMAIL_DOMAIN,
    seed_admin_org,
)

DEMO_ADMIN_EMAIL_LIKE = f"%@{EMAIL_DOMAIN}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 삭제/정규화를 커밋한다. 없으면 dry-run(미리보기 후 롤백).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = cleanup_demo_admins(db, apply=args.apply)
        mode = "APPLIED" if args.apply else "DRY-RUN (롤백됨, 변경 없음)"
        print(f"=== cleanup_demo_admins [{mode}] ===")
        print(f"  유지(목표 데모 관리자): {result['kept']}")
        print(f"  삭제 대상 데모 관리자 : {result['deleted']}")
        print(f"  신규 생성(누락 보충)  : {result['created']}")
        print(f"  등급/팀 정규화        : {result['normalized']}")
        print(f"  정리 후 활성 ADMIN 총 : {result['active_admins_after']}")
        if result["deleted_emails_sample"]:
            print(f"  삭제 예시(최대 5건)   : {result['deleted_emails_sample']}")
    finally:
        db.close()


def cleanup_demo_admins(db: Session, apply: bool) -> dict:
    """데모 관리자 조직을 목표 상태로 수렴시킨다(멱등).

    apply=False면 모든 변경을 롤백하고 미리보기 수치만 돌려준다.
    """
    # 1) 목표 조직 보장 + 남길 계정의 역할/팀/등급 정규화(OPS 승격 포함)
    org_result = seed_admin_org(db)

    # 2) 목표 조직에 없는 데모 관리자 식별
    delete_rows = db.execute(
        text(
            """
            SELECT user_id, email
            FROM users
            WHERE role = 'ADMIN'
              AND email LIKE :pattern
              AND email <> ALL(:keep)
            ORDER BY user_id
            """
        ),
        {"pattern": DEMO_ADMIN_EMAIL_LIKE, "keep": list(ADMIN_ORG_EMAILS)},
    ).fetchall()
    delete_ids = [row.user_id for row in delete_rows]
    delete_sample = [row.email for row in delete_rows[:5]]

    # 3) 하드 삭제 (FK CASCADE: user_roles / refresh_tokens 등 자동 정리)
    if delete_ids:
        db.execute(
            text("DELETE FROM users WHERE user_id = ANY(:ids)"),
            {"ids": delete_ids},
        )

    active_after = db.execute(
        text(
            "SELECT COUNT(*) FROM users "
            "WHERE role='ADMIN' AND is_deleted=false AND status='ACTIVE'"
        )
    ).scalar()

    result = {
        "kept": len(ADMIN_ORG_EMAILS),
        "deleted": len(delete_ids),
        "created": org_result["created"],
        "normalized": org_result["normalized"],
        "active_admins_after": active_after,
        "deleted_emails_sample": delete_sample,
    }

    if apply:
        db.commit()
    else:
        db.rollback()
    return result


if __name__ == "__main__":
    main()
