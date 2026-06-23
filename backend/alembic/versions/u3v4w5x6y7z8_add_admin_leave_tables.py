"""add admin leave request and balance tables

Revision ID: u3v4w5x6y7z8
Revises: t2u3v4w5x6y7
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa


revision = "u3v4w5x6y7z8"
down_revision = "t2u3v4w5x6y7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leave_balances",
        sa.Column("leave_balance_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="휴가 잔여 PK"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="관리자 user_id"),
        sa.Column("year", sa.Integer(), nullable=False, comment="휴가 기준 연도"),
        sa.Column("granted_days", sa.Numeric(6, 2), nullable=False, server_default="0", comment="부여 일수"),
        sa.Column("used_days", sa.Numeric(6, 2), nullable=False, server_default="0", comment="사용 확정 일수"),
        sa.Column("pending_days", sa.Numeric(6, 2), nullable=False, server_default="0", comment="승인 대기 일수"),
        sa.Column("remaining_days", sa.Numeric(6, 2), nullable=False, server_default="0", comment="잔여 가능 일수"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("leave_balance_id"),
        sa.UniqueConstraint("user_id", "year", name="uq_leave_balances_user_year"),
    )
    op.create_index("ix_leave_balances_user_id", "leave_balances", ["user_id"])
    op.create_index("ix_leave_balances_year", "leave_balances", ["year"])

    op.create_table(
        "admin_leave_requests",
        sa.Column("leave_request_id", sa.BigInteger(), autoincrement=True, nullable=False, comment="휴가 신청 PK"),
        sa.Column("requester_id", sa.BigInteger(), nullable=False, comment="신청자 user_id"),
        sa.Column("approver_id", sa.BigInteger(), nullable=True, comment="결재 예정/담당자 user_id"),
        sa.Column("leave_balance_id", sa.BigInteger(), nullable=True, comment="연결된 휴가 잔여 PK"),
        sa.Column("leave_type", sa.String(length=30), nullable=False, comment="휴가 종류"),
        sa.Column("start_date", sa.Date(), nullable=False, comment="휴가 시작일"),
        sa.Column("end_date", sa.Date(), nullable=False, comment="휴가 종료일"),
        sa.Column("start_half_day", sa.String(length=10), nullable=True, comment="시작일 반차 구분"),
        sa.Column("end_half_day", sa.String(length=10), nullable=True, comment="종료일 반차 구분"),
        sa.Column("requested_days", sa.Numeric(6, 2), nullable=False, comment="신청 일수"),
        sa.Column("reason", sa.String(length=1000), nullable=True, comment="신청 사유"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING", comment="신청 상태"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True, comment="승인 시각"),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True, comment="반려 시각"),
        sa.Column("reject_reason", sa.String(length=1000), nullable=True, comment="반려 사유"),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True, comment="취소 완료 시각"),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True, comment="취소 요청 시각"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="생성 시각"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="생성자 user_id"),
        sa.Column("created_ip", sa.String(length=45), nullable=True, comment="생성 요청 IP"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="최종 수정 시각"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="최종 수정자 user_id"),
        sa.Column("updated_ip", sa.String(length=45), nullable=True, comment="최종 수정 요청 IP"),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, comment="삭제 여부"),
        sa.ForeignKeyConstraint(["approver_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["leave_balance_id"], ["leave_balances.leave_balance_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("leave_request_id"),
    )
    op.create_index("ix_admin_leave_requests_requester_id", "admin_leave_requests", ["requester_id"])
    op.create_index("ix_admin_leave_requests_approver_id", "admin_leave_requests", ["approver_id"])
    op.create_index("ix_admin_leave_requests_leave_balance_id", "admin_leave_requests", ["leave_balance_id"])
    op.create_index("ix_admin_leave_requests_status", "admin_leave_requests", ["status"])
    op.create_index("ix_admin_leave_requests_start_date", "admin_leave_requests", ["start_date"])


def downgrade() -> None:
    op.drop_index("ix_admin_leave_requests_start_date", table_name="admin_leave_requests")
    op.drop_index("ix_admin_leave_requests_status", table_name="admin_leave_requests")
    op.drop_index("ix_admin_leave_requests_leave_balance_id", table_name="admin_leave_requests")
    op.drop_index("ix_admin_leave_requests_approver_id", table_name="admin_leave_requests")
    op.drop_index("ix_admin_leave_requests_requester_id", table_name="admin_leave_requests")
    op.drop_table("admin_leave_requests")

    op.drop_index("ix_leave_balances_year", table_name="leave_balances")
    op.drop_index("ix_leave_balances_user_id", table_name="leave_balances")
    op.drop_table("leave_balances")
