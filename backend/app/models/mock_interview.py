"""채팅형 모의면접 세션과 턴 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin, RegModAuditMixin


MOCK_INTERVIEW_STATUS_IN_PROGRESS = "IN_PROGRESS"
MOCK_INTERVIEW_STATUS_COMPLETED = "COMPLETED"
MOCK_INTERVIEW_STATUS_ABANDONED = "ABANDONED"

MOCK_INTERVIEW_STATUS_VALUES = {
    MOCK_INTERVIEW_STATUS_IN_PROGRESS,
    MOCK_INTERVIEW_STATUS_COMPLETED,
    MOCK_INTERVIEW_STATUS_ABANDONED,
}

MOCK_INTERVIEW_STAGE_WARMUP = "WARMUP"
MOCK_INTERVIEW_STAGE_EXPERIENCE = "EXPERIENCE"
MOCK_INTERVIEW_STAGE_DEEP = "DEEP"
MOCK_INTERVIEW_STAGE_COMPLETED = "COMPLETED"

MOCK_INTERVIEW_STAGE_VALUES = {
    MOCK_INTERVIEW_STAGE_WARMUP,
    MOCK_INTERVIEW_STAGE_EXPERIENCE,
    MOCK_INTERVIEW_STAGE_DEEP,
    MOCK_INTERVIEW_STAGE_COMPLETED,
}


class MockInterviewSession(Base, AuditMixin, RegModAuditMixin):
    """한 번의 채팅형 모의면접 진행 상태."""

    __tablename__ = "mock_interview_sessions"

    session_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="모의면접 세션 PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="소유자 user_id",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용한 이력서 resume_id",
    )
    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("job_postings.job_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용한 공고 job_id",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MOCK_INTERVIEW_STATUS_IN_PROGRESS,
        server_default=MOCK_INTERVIEW_STATUS_IN_PROGRESS,
        index=True,
        comment="진행 상태",
    )
    stage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MOCK_INTERVIEW_STAGE_WARMUP,
        server_default=MOCK_INTERVIEW_STAGE_WARMUP,
        index=True,
        comment="현재 단계",
    )
    question_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="생성된 질문 수",
    )
    total_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="종료 후 종합 점수",
    )
    summary: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="종료 후 종합 리포트",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="종료 시각",
    )


class MockInterviewTurn(Base, AuditMixin, RegModAuditMixin):
    """채팅형 모의면접의 질문과 답변 한 묶음."""

    __tablename__ = "mock_interview_turns"

    turn_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="모의면접 턴 PK",
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("mock_interview_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="부모 세션",
    )
    turn_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="질문 순서",
    )
    stage: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="질문 단계",
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="면접 질문",
    )
    user_answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="사용자 답변",
    )
    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="답변 피드백",
    )
    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="내부 답변 점수",
    )
    based_on_chunk: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="내부 RAG 근거",
    )
