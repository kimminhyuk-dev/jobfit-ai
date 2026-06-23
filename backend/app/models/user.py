"""
User 모델
회원 정보를 담는 테이블
"""

from datetime import date

from sqlalchemy import JSON, BigInteger, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class User(Base, AuditMixin, SoftDeleteMixin):
    """
    회원 테이블
    - 내부 PK: user_id (BIGINT, 자동증가)
    - 로그인 ID: email (UNIQUE)
    - 비밀번호: bcrypt 해시 저장 (평문 절대 금지)
    - 감사 컬럼: AuditMixin에서 상속
    - 소프트 삭제: SoftDeleteMixin에서 상속
    """

    __tablename__ = "users"

    # 기본 식별자
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="회원 내부 PK",
    )

    # 로그인 정보
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="로그인 ID (이메일)",
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="비밀번호 해시 (bcrypt)",
    )

    # 프로필
    name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="이름",
    )
    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="생년월일",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="전화번호 (010-1234-5678 형식 정규화 저장)",
    )
    gender: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="성별: MALE / FEMALE",
    )
    zipcode: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="우편번호 (5자리, 주소검색 API)",
    )
    address1: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="기본주소 (주소검색 API 자동입력)",
    )
    address2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="상세주소 (사용자 입력)",
    )
    tech_stack: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="기술스택 문자열 배열",
    )

    # 상태
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        comment="계정 상태: ACTIVE / LOCKED / DORMANT",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="USER",
        server_default="USER",
        comment="권한: USER / COMPANY / ADMIN",
    )
    admin_level: Mapped[str | None] = mapped_column(
        String(1),
        nullable=True,
        comment="관리자 등급 (ADMIN 전용): A / B / C. "
        "A=B·C 권한부여+계정삭제, B=C 권한부여, C=기본 관리자",
    )

    # 조직(팀) — 휴가 결재선 계산용
    team_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("teams.team_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="소속 팀 team_id (결재선 계산용)",
    )
    team_role: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="팀 내 역할: LEAD / MEMBER",
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email})>"
