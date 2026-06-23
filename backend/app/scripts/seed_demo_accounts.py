"""Seed deterministic demo accounts for admin/user/company roles.

관리자(ADMIN)는 더 이상 --count-per-role 규모로 대량 생성하지 않는다.
현업에 가까운 고정 조직 구조(ADMIN_ORG)로만 시드하며, USER/COMPANY 데모
규모와는 분리(decouple)되어 있다.

- 관리자 조직(고정):
    SUPER_ADMIN 2명(본사, 팀 없음)
    OPS_ADMIN   1명(운영, 팀 없음)
    팀당 TEAM_LEAD 1명 + ADMIN_STAFF 4명 (데모 팀 3개)
  => 데모 관리자 총 18명. NULL 등급 실관리자 등 비데모 계정은 건드리지 않는다.
- USER / COMPANY: --count-per-role 규모로 시드(기본 243, 기존 데모 규모 유지).

모든 시드는 멱등(idempotent)하다 — 여러 번 실행해도 중복 row가 쌓이지 않는다.

Usage:
    python -m app.scripts.seed_demo_accounts                 # admin 조직 + user/company 243
    python -m app.scripts.seed_demo_accounts --count-per-role 50
    python -m app.scripts.seed_demo_accounts --skip-users    # 관리자 조직만 시드
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.company import Company
from app.models.rbac import (
    ROLE_ADMIN_STAFF,
    ROLE_OPS_ADMIN,
    ROLE_SUPER_ADMIN,
    ROLE_TEAM_LEAD,
)
from app.models.team import TEAM_ROLE_LEAD, TEAM_ROLE_MEMBER
from app.models.user import User

# Demo-only seed password for local/portfolio accounts.
DEMO_PASSWORD = "admin1234"
EMAIL_DOMAIN = "demo.jobfit.local"

# 데모 팀 이름/순서 (t2 마이그레이션과 동일하게 유지).
DEMO_TEAM_NAMES = ["채용운영팀", "회원지원팀", "플랫폼관리팀"]
DEMO_TEAM_DESCRIPTIONS = {
    "채용운영팀": "채용공고와 지원자 운영을 담당하는 데모 팀",
    "회원지원팀": "회원 지원과 관리자 업무를 담당하는 데모 팀",
    "플랫폼관리팀": "플랫폼 운영과 내부 결재를 담당하는 데모 팀",
}

KOREAN_NAMES = [
    "김민준",
    "이서연",
    "박지훈",
    "최유진",
    "정현우",
    "강수아",
    "조민재",
    "윤하은",
    "장도윤",
    "임지아",
    "한서준",
    "오예린",
]

COMPANY_WORDS = [
    "넥스트",
    "브릿지",
    "플로우",
    "스케일",
    "픽셀",
    "모션",
    "루트",
    "클라우드",
    "데이터",
    "인사이트",
    "커넥트",
    "랩스",
]

TECH_STACKS = [
    ["Python", "FastAPI", "PostgreSQL"],
    ["Java", "Spring Boot", "MySQL"],
    ["React", "TypeScript", "Next.js"],
    ["Kotlin", "Android", "Compose"],
    ["Swift", "iOS", "UIKit"],
    ["AWS", "Docker", "Kubernetes"],
    ["Python", "Airflow", "Spark"],
    ["JavaScript", "Node.js", "MongoDB"],
]


@dataclass(frozen=True)
class AdminSpec:
    """데모 관리자 1명의 목표 상태(역할/팀/등급)."""

    email_local: str
    admin_level: str
    role_codes: tuple[str, ...]
    team_name: str | None
    team_role: str | None

    @property
    def email(self) -> str:
        return f"{self.email_local}@{EMAIL_DOMAIN}"


def _build_admin_org() -> list[AdminSpec]:
    """현업에 가까운 데모 관리자 조직(고정)을 구성한다.

    기존 정리 승인 분류와 동일한 계정 이메일을 사용해, 정리 스크립트로 남긴
    계정과 신규 시드가 같은 계정으로 수렴하게 한다.
    OPS_ADMIN은 권한 계열이 ADMIN_STAFF와 같아 레거시 셰임과 충돌하지 않도록
    admin_level을 'C'로 둔다(셰임 C -> ADMIN_STAFF == OPS_ADMIN 권한).
    """
    specs: list[AdminSpec] = [
        AdminSpec("admin001", "A", (ROLE_SUPER_ADMIN,), None, None),
        AdminSpec("admin004", "A", (ROLE_SUPER_ADMIN,), None, None),
        AdminSpec("admin007", "C", (ROLE_OPS_ADMIN,), None, None),
    ]
    lead_locals = ["admin002", "admin005", "admin008"]
    staff_locals = [
        ["admin003", "admin012", "admin021", "admin030"],
        ["admin006", "admin015", "admin024", "admin033"],
        ["admin009", "admin018", "admin027", "admin036"],
    ]
    for team_index, team_name in enumerate(DEMO_TEAM_NAMES):
        specs.append(
            AdminSpec(
                lead_locals[team_index],
                "B",
                (ROLE_TEAM_LEAD, ROLE_ADMIN_STAFF),
                team_name,
                TEAM_ROLE_LEAD,
            )
        )
        for staff_local in staff_locals[team_index]:
            specs.append(
                AdminSpec(
                    staff_local,
                    "C",
                    (ROLE_ADMIN_STAFF,),
                    team_name,
                    TEAM_ROLE_MEMBER,
                )
            )
    return specs


ADMIN_ORG: list[AdminSpec] = _build_admin_org()
ADMIN_ORG_EMAILS: set[str] = {spec.email for spec in ADMIN_ORG}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--count-per-role",
        type=int,
        default=243,
        help="시드할 데모 USER/COMPANY 수(관리자 조직과는 분리).",
    )
    parser.add_argument(
        "--skip-users",
        action="store_true",
        help="USER/COMPANY 시드를 건너뛰고 관리자 조직만 시드.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        admin_result = seed_admin_org(db)
        user_result = {"users": 0, "companies": 0}
        if not args.skip_users:
            user_result = seed_demo_users_companies(db, count=args.count_per_role)
        db.commit()
        print(
            "demo admin org seeded: "
            f"created={admin_result['created']}, normalized={admin_result['normalized']}, "
            f"total_spec={len(ADMIN_ORG)}"
        )
        print(
            "demo accounts seeded: "
            f"users={user_result['users']}, companies={user_result['companies']}"
        )
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()


def seed_admin_org(db: Session) -> dict[str, int]:
    """데모 관리자 조직을 목표 상태로 보장한다(멱등, commit은 호출자가 수행)."""
    team_ids = _ensure_demo_teams(db)
    role_ids = _resolve_role_ids(db, {code for spec in ADMIN_ORG for code in spec.role_codes})
    hashed_password = hash_password(DEMO_PASSWORD)

    created = 0
    normalized = 0
    for spec in ADMIN_ORG:
        team_id = team_ids[spec.team_name] if spec.team_name else None
        user = _get_user_by_email(db, spec.email)
        if user is None:
            user = User(
                email=spec.email,
                password=hashed_password,
                name=_admin_display_name(spec),
                role="ADMIN",
                admin_level=spec.admin_level,
                status="ACTIVE",
                team_id=team_id,
                team_role=spec.team_role,
                created_ip="127.0.0.1",
                updated_ip="127.0.0.1",
            )
            db.add(user)
            db.flush()
            created += 1
        else:
            # 기존 데모 관리자는 이름/비밀번호는 보존하고 등급/팀만 목표값으로 맞춘다.
            if (
                user.admin_level != spec.admin_level
                or user.team_id != team_id
                or user.team_role != spec.team_role
                or user.role != "ADMIN"
            ):
                user.role = "ADMIN"
                user.admin_level = spec.admin_level
                user.team_id = team_id
                user.team_role = spec.team_role
                normalized += 1

        _sync_user_roles(db, user.user_id, {role_ids[code] for code in spec.role_codes})

    return {"created": created, "normalized": normalized}


def seed_demo_users_companies(db: Session, count: int) -> dict[str, int]:
    """데모 USER/COMPANY 계정을 시드한다(멱등, commit은 호출자가 수행)."""
    hashed_password = hash_password(DEMO_PASSWORD)
    created = {"users": 0, "companies": 0}
    for index in range(1, count + 1):
        if _ensure_user(db, index, hashed_password):
            created["users"] += 1
        if _ensure_company(db, index, hashed_password):
            created["companies"] += 1
    return created


def _ensure_demo_teams(db: Session) -> dict[str, int]:
    """데모 팀 3개를 보장하고 이름->team_id 매핑을 돌려준다(멱등)."""
    for name in DEMO_TEAM_NAMES:
        db.execute(
            text(
                """
                INSERT INTO teams (name, description, is_active, is_deleted)
                SELECT CAST(:name AS VARCHAR), CAST(:description AS VARCHAR), true, false
                WHERE NOT EXISTS (
                    SELECT 1 FROM teams WHERE name = :name AND is_deleted = false
                )
                """
            ),
            {"name": name, "description": DEMO_TEAM_DESCRIPTIONS[name]},
        )
    rows = db.execute(
        text(
            "SELECT name, team_id FROM teams "
            "WHERE name = ANY(:names) AND is_deleted = false"
        ),
        {"names": DEMO_TEAM_NAMES},
    ).fetchall()
    return {name: team_id for name, team_id in rows}


def _resolve_role_ids(db: Session, role_codes: set[str]) -> dict[str, int]:
    """역할 코드 -> role_id 매핑을 조회한다. 누락 시 명확한 오류를 던진다."""
    rows = db.execute(
        text("SELECT code, role_id FROM roles WHERE code = ANY(:codes)"),
        {"codes": list(role_codes)},
    ).fetchall()
    found = {code: role_id for code, role_id in rows}
    missing = role_codes - set(found)
    if missing:
        raise RuntimeError(
            f"필요한 역할이 시드되지 않았습니다: {sorted(missing)}. "
            "먼저 'alembic upgrade head'를 실행하세요."
        )
    return found


def _sync_user_roles(db: Session, user_id: int, desired_role_ids: set[int]) -> None:
    """사용자의 user_roles를 목표 집합과 정확히 일치시킨다(멱등)."""
    existing = set(
        db.execute(
            text("SELECT role_id FROM user_roles WHERE user_id = :uid"),
            {"uid": user_id},
        ).scalars()
    )
    to_remove = existing - desired_role_ids
    to_add = desired_role_ids - existing
    if to_remove:
        db.execute(
            text(
                "DELETE FROM user_roles WHERE user_id = :uid AND role_id = ANY(:rids)"
            ),
            {"uid": user_id, "rids": list(to_remove)},
        )
    for role_id in to_add:
        db.execute(
            text(
                "INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid) "
                "ON CONFLICT (user_id, role_id) DO NOTHING"
            ),
            {"uid": user_id, "rid": role_id},
        )


def _admin_display_name(spec: AdminSpec) -> str:
    if ROLE_SUPER_ADMIN in spec.role_codes:
        return "최고관리자"
    if ROLE_OPS_ADMIN in spec.role_codes:
        return "운영관리자"
    if spec.team_role == TEAM_ROLE_LEAD:
        return f"{spec.team_name} 팀장"
    return f"{spec.team_name} 담당자"


def _ensure_user(db: Session, index: int, hashed_password: str) -> bool:
    email = f"user{index:03d}@{EMAIL_DOMAIN}"
    if _user_exists(db, email):
        return False

    name = f"{KOREAN_NAMES[(index - 1) % len(KOREAN_NAMES)]}{index:03d}"
    user = User(
        email=email,
        password=hashed_password,
        name=name,
        role="USER",
        status="ACTIVE",
        birth_date=_birth_date(index),
        phone=f"010-{1000 + index:04d}-{2000 + index:04d}",
        gender="MALE" if index % 2 else "FEMALE",
        zipcode=f"{10000 + (index % 89999):05d}",
        address1=f"서울특별시 강남구 테헤란로 {index}",
        address2=f"{index:03d}호",
        tech_stack=TECH_STACKS[(index - 1) % len(TECH_STACKS)],
        created_ip="127.0.0.1",
        updated_ip="127.0.0.1",
    )
    db.add(user)
    return True


def _ensure_company(db: Session, index: int, hashed_password: str) -> bool:
    email = f"company{index:03d}@{EMAIL_DOMAIN}"
    existing_user = _get_user_by_email(db, email)
    if existing_user is not None:
        _sync_existing_company(db, existing_user, index)
        return False

    company_name = f"{COMPANY_WORDS[(index - 1) % len(COMPANY_WORDS)]}{index:03d} 주식회사"
    business_number = _business_number_from_seed(520100000 + index)
    representative = f"{KOREAN_NAMES[(index + 3) % len(KOREAN_NAMES)]}{index:03d}"

    user = User(
        email=email,
        password=hashed_password,
        name=representative,
        role="COMPANY",
        status="ACTIVE",
        phone=f"010-{3000 + index:04d}-{4000 + index:04d}",
        zipcode=f"{20000 + (index % 69999):05d}",
        address1=f"서울특별시 금천구 디지털로 {index}",
        address2=f"{company_name} 본사",
        created_ip="127.0.0.1",
        updated_ip="127.0.0.1",
    )
    db.add(user)
    db.flush()

    company = Company(
        user_id=user.user_id,
        company_name=company_name,
        business_number=business_number,
        dedup_key=f"bn:{business_number}",
        created_ip="127.0.0.1",
        updated_ip="127.0.0.1",
    )
    db.add(company)
    return True


def _user_exists(db: Session, email: str) -> bool:
    return _get_user_by_email(db, email) is not None


def _get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email).limit(1)
    return db.execute(stmt).scalar_one_or_none()


def _sync_existing_company(db: Session, user: User, index: int) -> None:
    company_name = f"{COMPANY_WORDS[(index - 1) % len(COMPANY_WORDS)]}{index:03d} 주식회사"
    business_number = _business_number_from_seed(520100000 + index)
    stmt = (
        select(Company)
        .where(Company.user_id == user.user_id)
        .where(Company.is_deleted.is_(False))
        .limit(1)
    )
    company = db.execute(stmt).scalar_one_or_none()
    if company is None:
        return
    company.company_name = company_name
    company.business_number = business_number
    company.dedup_key = f"bn:{business_number}"


def _business_number_from_seed(first_nine_digits: int) -> str:
    digits = [int(ch) for ch in f"{first_nine_digits:09d}"]
    weights = [1, 3, 7, 1, 3, 7, 1, 3]
    total = sum(digit * weight for digit, weight in zip(digits[:8], weights))
    last_product = digits[8] * 5
    total += last_product // 10 + last_product % 10
    check_digit = (10 - (total % 10)) % 10
    return "".join(str(digit) for digit in [*digits, check_digit])


def _birth_date(index: int) -> date:
    year = 1975 + (index % 30)
    month = (index % 12) + 1
    day = (index % 27) + 1
    return date(year, month, day)


if __name__ == "__main__":
    main()
