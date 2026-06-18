"""DB access for application matching scores."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_match_score import ApplicationMatchScore


class ApplicationMatchScoreRepository:
    """Persistence operations for stored application match scores."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_application_id(
        self,
        application_id: int,
    ) -> ApplicationMatchScore | None:
        stmt = select(ApplicationMatchScore).where(
            ApplicationMatchScore.application_id == application_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_application_ids(
        self,
        application_ids: list[int],
    ) -> dict[int, ApplicationMatchScore]:
        if not application_ids:
            return {}
        stmt = select(ApplicationMatchScore).where(
            ApplicationMatchScore.application_id.in_(application_ids)
        )
        scores = self.db.execute(stmt).scalars().all()
        return {score.application_id: score for score in scores}

    def upsert(
        self,
        *,
        application_id: int,
        score: int,
        grade: str,
        summary: str,
        strengths: list[str],
        gaps: list[str],
        matched_skills: list[str],
        missing_skills: list[str],
        evidence: dict[str, Any],
        model: str,
        algorithm_version: str,
        input_signature: str,
        actor_id: int | None,
        request_ip: str | None,
    ) -> ApplicationMatchScore:
        existing = self.get_by_application_id(application_id)
        if existing is None:
            existing = ApplicationMatchScore(
                application_id=application_id,
                created_by=actor_id,
                created_ip=request_ip,
            )
            self.db.add(existing)

        existing.score = score
        existing.grade = grade
        existing.summary = summary
        existing.strengths = strengths
        existing.gaps = gaps
        existing.matched_skills = matched_skills
        existing.missing_skills = missing_skills
        existing.evidence = evidence
        existing.model = model
        existing.algorithm_version = algorithm_version
        existing.input_signature = input_signature
        existing.updated_by = actor_id
        existing.updated_ip = request_ip
        self.db.flush()
        return existing
