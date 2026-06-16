"""Seed deterministic demo accounts for admin/user/company roles.

Usage:
    python -m app.scripts.seed_demo_accounts --count-per-role 243
"""

from __future__ import annotations

import argparse
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User

DEMO_PASSWORD = "admin1234"
EMAIL_DOMAIN = "demo.jobfit.local"

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count-per-role", type=int, default=243)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = seed_demo_accounts(db, count_per_role=args.count_per_role)
        print(
            "demo accounts seeded: "
            f"admins={result['admins']}, users={result['users']}, companies={result['companies']}"
        )
    finally:
        db.close()


def seed_demo_accounts(db: Session, count_per_role: int) -> dict[str, int]:
    hashed_password = hash_password(DEMO_PASSWORD)
    created = {"admins": 0, "users": 0, "companies": 0}

    try:
        for index in range(1, count_per_role + 1):
            if _ensure_admin(db, index, hashed_password):
                created["admins"] += 1
            if _ensure_user(db, index, hashed_password):
                created["users"] += 1
            if _ensure_company(db, index, hashed_password):
                created["companies"] += 1
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    return created


def _ensure_admin(db: Session, index: int, hashed_password: str) -> bool:
    email = f"admin{index:03d}@{EMAIL_DOMAIN}"
    if _user_exists(db, email):
        return False

    level = ("A", "B", "C")[(index - 1) % 3]
    user = User(
        email=email,
        password=hashed_password,
        name=f"관리자{index:03d}",
        role="ADMIN",
        admin_level=level,
        status="ACTIVE",
        created_ip="127.0.0.1",
        updated_ip="127.0.0.1",
    )
    db.add(user)
    return True


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
