"""관리자 휴가 신청/잔여일 DB 접근 계층."""

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.admin_leave import (
    AdminLeaveRequest,
    LeaveBalance,
    LEAVE_STATUS_CANCEL_REQUESTED,
    LEAVE_STATUS_PENDING,
)
from app.models.team import TEAM_ROLE_LEAD
from app.models.user import User


class AdminLeaveRepository:
    """관리자 휴가 신청과 잔여일 저장소."""

    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> User | None:
        """활성 사용자를 조회한다."""
        stmt = (
            select(User)
            .where(User.user_id == user_id)
            .where(User.is_deleted.is_(False))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_team_lead(self, *, team_id: int, exclude_user_id: int) -> User | None:
        """같은 팀의 팀장을 한 명 조회한다."""
        stmt = (
            select(User)
            .where(User.role == "ADMIN")
            .where(User.status == "ACTIVE")
            .where(User.is_deleted.is_(False))
            .where(User.team_id == team_id)
            .where(User.team_role == TEAM_ROLE_LEAD)
            .where(User.user_id != exclude_user_id)
            .order_by(User.user_id.asc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_super_admin(self, *, exclude_user_id: int) -> User | None:
        """다른 최고 관리자를 한 명 조회한다."""
        stmt = (
            select(User)
            .where(User.role == "ADMIN")
            .where(User.status == "ACTIVE")
            .where(User.is_deleted.is_(False))
            .where(User.admin_level == "A")
            .where(User.user_id != exclude_user_id)
            .order_by(User.user_id.asc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_balance(self, *, user_id: int, year: int) -> LeaveBalance | None:
        """연도별 잔여일을 잠금 없이 조회한다(조회 전용)."""
        stmt = (
            select(LeaveBalance)
            .where(LeaveBalance.user_id == user_id)
            .where(LeaveBalance.year == year)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_balance_for_update(self, *, user_id: int, year: int) -> LeaveBalance | None:
        """연도별 잔여일을 잠금 조회한다."""
        stmt = (
            select(LeaveBalance)
            .where(LeaveBalance.user_id == user_id)
            .where(LeaveBalance.year == year)
            .with_for_update()
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_balance_by_id_for_update(self, leave_balance_id: int) -> LeaveBalance | None:
        """잔여일을 PK로 잠금 조회한다."""
        stmt = (
            select(LeaveBalance)
            .where(LeaveBalance.leave_balance_id == leave_balance_id)
            .with_for_update()
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_balance(
        self,
        *,
        user_id: int,
        year: int,
        granted_days,
        actor_id: int,
        request_ip: str | None,
    ) -> LeaveBalance:
        """연도별 잔여일을 생성한다."""
        balance = LeaveBalance(
            user_id=user_id,
            year=year,
            granted_days=granted_days,
            used_days=0,
            pending_days=0,
            remaining_days=granted_days,
            created_by=actor_id,
            updated_by=actor_id,
            created_ip=request_ip,
            updated_ip=request_ip,
        )
        self.db.add(balance)
        self.db.flush()
        return balance

    def create_request(
        self,
        *,
        requester_id: int,
        approver_id: int,
        leave_balance_id: int,
        leave_type: str,
        start_date: date,
        end_date: date,
        start_half_day: str | None,
        end_half_day: str | None,
        requested_days,
        reason: str | None,
        actor_id: int,
        request_ip: str | None,
    ) -> AdminLeaveRequest:
        """휴가 신청을 생성한다."""
        leave_request = AdminLeaveRequest(
            requester_id=requester_id,
            approver_id=approver_id,
            leave_balance_id=leave_balance_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            start_half_day=start_half_day,
            end_half_day=end_half_day,
            requested_days=requested_days,
            reason=reason,
            created_by=actor_id,
            updated_by=actor_id,
            created_ip=request_ip,
            updated_ip=request_ip,
        )
        self.db.add(leave_request)
        self.db.flush()
        return leave_request

    def get_request_for_update(self, leave_request_id: int) -> AdminLeaveRequest | None:
        """휴가 신청을 잠금 조회한다."""
        stmt = (
            select(AdminLeaveRequest)
            .where(AdminLeaveRequest.leave_request_id == leave_request_id)
            .where(AdminLeaveRequest.is_deleted.is_(False))
            .with_for_update()
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_requester(self, requester_id: int) -> list[AdminLeaveRequest]:
        """신청자 기준 목록을 최신순으로 조회한다."""
        stmt = (
            select(AdminLeaveRequest)
            .where(AdminLeaveRequest.requester_id == requester_id)
            .where(AdminLeaveRequest.is_deleted.is_(False))
            .order_by(AdminLeaveRequest.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_pending_for_approver(self, approver_id: int) -> list[AdminLeaveRequest]:
        """결재자가 처리해야 할 신청 목록을 조회한다."""
        stmt = (
            select(AdminLeaveRequest)
            .where(AdminLeaveRequest.approver_id == approver_id)
            .where(AdminLeaveRequest.is_deleted.is_(False))
            .where(
                or_(
                    AdminLeaveRequest.status == LEAVE_STATUS_PENDING,
                    AdminLeaveRequest.status == LEAVE_STATUS_CANCEL_REQUESTED,
                )
            )
            .order_by(AdminLeaveRequest.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_users_by_ids(self, user_ids: set[int]) -> dict[int, User]:
        """여러 사용자 정보를 한 번에 조회한다."""
        if not user_ids:
            return {}
        stmt = select(User).where(User.user_id.in_(user_ids))
        users = self.db.execute(stmt).scalars().all()
        return {user.user_id: user for user in users}
