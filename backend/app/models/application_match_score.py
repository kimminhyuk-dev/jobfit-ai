"""Application matching score model."""

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import AuditMixin


class ApplicationMatchScore(Base, AuditMixin):
    """Stored resume-to-job matching score for one application."""

    __tablename__ = "application_match_scores"

    match_score_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Match score PK",
    )
    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("applications.application_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Scored application id",
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="0-100 matching score",
    )
    grade: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="Matching grade A/B/C/D",
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="Short score rationale",
    )
    strengths: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="Positive matching factors",
    )
    gaps: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="Missing or weak matching factors",
    )
    matched_skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="Skills found on both resume and job posting",
    )
    missing_skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment="Job skills not found on the resume",
    )
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Scoring component details",
    )
    model: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Scoring model or algorithm name",
    )
    algorithm_version: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        comment="Scoring algorithm version",
    )
    input_signature: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 signature of scored input fields",
    )

    def __repr__(self) -> str:
        return (
            f"<ApplicationMatchScore(application_id={self.application_id}, "
            f"score={self.score}, grade={self.grade!r})>"
        )
