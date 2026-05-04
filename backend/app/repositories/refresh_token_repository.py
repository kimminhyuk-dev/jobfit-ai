"""
Refresh Token DB 접근 계층
"""

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
        created_ip: str | None,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
            created_ip=created_ip,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """취소·만료 여부 무관하게 해시로 조회 (재사용 감지용)."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_active_by_hash(self, token_hash: str) -> RefreshToken | None:
        """활성 상태(미취소 + 미만료)인 토큰을 조회한다."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.is_revoked.is_(False))
            .where(RefreshToken.expires_at > now)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke(self, token: RefreshToken) -> None:
        token.is_revoked = True
        self.db.flush()

    def revoke_family(self, family_id: str) -> None:
        """동일 패밀리의 모든 토큰을 취소한다 (재사용 공격 대응)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .values(is_revoked=True)
        )
        self.db.execute(stmt)
        self.db.flush()

    def revoke_all_by_user(self, user_id: int) -> None:
        """회원의 모든 Refresh Token을 취소한다 (비밀번호 변경·강제 로그아웃)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        self.db.execute(stmt)
        self.db.flush()
