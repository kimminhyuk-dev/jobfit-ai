"""SQLAlchemy models for resume interview practice sessions."""

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class ResumeInterviewSession(Base, AuditMixin):
    """Interview practice session generated from one resume."""

    __tablename__ = "resume_interview_sessions"

    session_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Interview session PK",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user_id",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source resume_id",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="IN_PROGRESS",
        server_default="IN_PROGRESS",
        index=True,
        comment="IN_PROGRESS / COMPLETED",
    )
    model: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="OpenAI model used for question generation",
    )
    total_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Sum of submitted answer scores",
    )
    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default="100",
        comment="Maximum session score",
    )


class ResumeInterviewQuestion(Base, AuditMixin):
    """One generated interview question inside a session."""

    __tablename__ = "resume_interview_questions"

    question_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Interview question PK",
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resume_interview_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent interview session",
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Display order from 1 to 5",
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Interview question text",
    )
    question_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
        comment="PROJECT / TECH_STACK / EXPERIENCE / COVER_LETTER / JOB_FIT",
    )
    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Question source category",
    )
    intent: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Question intent",
    )
    difficulty: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Question difficulty",
    )
    expected_keywords: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Expected answer keywords",
    )
    official_references: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Allowed official references for this question",
    )
    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
        server_default="20",
        comment="Maximum question score",
    )


class ResumeInterviewAnswer(Base, AuditMixin):
    """User answer and model evaluation for one question."""

    __tablename__ = "resume_interview_answers"

    answer_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Interview answer PK",
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resume_interview_questions.question_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Answered question",
    )
    user_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Submitted user answer",
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Evaluated score",
    )
    max_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
        server_default="20",
        comment="Maximum answer score",
    )
    verdict: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="GOOD / PARTIAL / INSUFFICIENT / UNKNOWN",
    )
    strengths: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Correct or strong answer points",
    )
    missing_points: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Missing answer points",
    )
    incorrect_points: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Incorrect answer points",
    )
    feedback: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Actionable feedback",
    )
    reference_based_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Reference-based improved answer",
    )
    official_references_used: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Official references used in evaluation",
    )
    model: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="OpenAI model used for answer evaluation",
    )
