"""Database access for resume interview practice."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.resume_interview import (
    ResumeInterviewAnswer,
    ResumeInterviewQuestion,
    ResumeInterviewSession,
)


class InterviewPracticeRepository:
    """Persistence operations for interview practice sessions."""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        *,
        user_id: int,
        resume_id: int,
        model: str,
        max_score: int,
        actor_id: int,
        request_ip: str | None,
    ) -> ResumeInterviewSession:
        session = ResumeInterviewSession(
            user_id=user_id,
            resume_id=resume_id,
            status="IN_PROGRESS",
            model=model,
            total_score=None,
            max_score=max_score,
            created_by=actor_id,
            created_ip=request_ip,
            updated_by=actor_id,
            updated_ip=request_ip,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def create_questions(
        self,
        *,
        session_id: int,
        questions: list[dict[str, Any]],
        actor_id: int,
        request_ip: str | None,
    ) -> list[ResumeInterviewQuestion]:
        rows: list[ResumeInterviewQuestion] = []
        for item in questions:
            row = ResumeInterviewQuestion(
                session_id=session_id,
                display_order=item["display_order"],
                question=item["question"],
                question_type=item["question_type"],
                source=item["source"],
                intent=item["intent"],
                difficulty=item["difficulty"],
                expected_keywords=item.get("expected_keywords") or [],
                official_references=item.get("official_references") or [],
                max_score=item.get("max_score") or 20,
                created_by=actor_id,
                created_ip=request_ip,
                updated_by=actor_id,
                updated_ip=request_ip,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def get_session_for_user(
        self,
        *,
        session_id: int,
        resume_id: int,
        user_id: int,
    ) -> ResumeInterviewSession | None:
        stmt = select(ResumeInterviewSession).where(
            ResumeInterviewSession.session_id == session_id,
            ResumeInterviewSession.resume_id == resume_id,
            ResumeInterviewSession.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_questions(self, session_id: int) -> list[ResumeInterviewQuestion]:
        stmt = (
            select(ResumeInterviewQuestion)
            .where(ResumeInterviewQuestion.session_id == session_id)
            .order_by(ResumeInterviewQuestion.display_order)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_answers_by_question_ids(
        self,
        question_ids: list[int],
    ) -> dict[int, ResumeInterviewAnswer]:
        if not question_ids:
            return {}
        stmt = select(ResumeInterviewAnswer).where(
            ResumeInterviewAnswer.question_id.in_(question_ids)
        )
        answers = self.db.execute(stmt).scalars().all()
        return {answer.question_id: answer for answer in answers}

    def get_question_for_user(
        self,
        *,
        question_id: int,
        resume_id: int,
        user_id: int,
    ) -> ResumeInterviewQuestion | None:
        stmt = (
            select(ResumeInterviewQuestion)
            .join(
                ResumeInterviewSession,
                ResumeInterviewSession.session_id
                == ResumeInterviewQuestion.session_id,
            )
            .where(
                ResumeInterviewQuestion.question_id == question_id,
                ResumeInterviewSession.resume_id == resume_id,
                ResumeInterviewSession.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_answer_for_question(
        self,
        question_id: int,
    ) -> ResumeInterviewAnswer | None:
        stmt = select(ResumeInterviewAnswer).where(
            ResumeInterviewAnswer.question_id == question_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def save_answer(
        self,
        *,
        question_id: int,
        user_answer: str,
        score: int,
        max_score: int,
        verdict: str,
        strengths: list[str],
        missing_points: list[str],
        incorrect_points: list[str],
        feedback: str,
        reference_based_answer: str,
        official_references_used: list[dict[str, Any]],
        model: str,
        actor_id: int,
        request_ip: str | None,
    ) -> ResumeInterviewAnswer:
        answer = self.get_answer_for_question(question_id)
        if answer is None:
            answer = ResumeInterviewAnswer(
                question_id=question_id,
                created_by=actor_id,
                created_ip=request_ip,
            )
            self.db.add(answer)

        answer.user_answer = user_answer
        answer.score = score
        answer.max_score = max_score
        answer.verdict = verdict
        answer.strengths = strengths
        answer.missing_points = missing_points
        answer.incorrect_points = incorrect_points
        answer.feedback = feedback
        answer.reference_based_answer = reference_based_answer
        answer.official_references_used = official_references_used
        answer.model = model
        answer.updated_by = actor_id
        answer.updated_ip = request_ip
        self.db.flush()
        return answer

    def update_session_score(
        self,
        *,
        session_id: int,
        actor_id: int,
        request_ip: str | None,
    ) -> ResumeInterviewSession | None:
        session = self.db.get(ResumeInterviewSession, session_id)
        if session is None:
            return None

        questions = self.list_questions(session_id)
        question_ids = [q.question_id for q in questions]
        answers = self.list_answers_by_question_ids(question_ids)
        score_total = sum(answer.score for answer in answers.values())
        max_total = sum(question.max_score for question in questions)

        session.total_score = score_total if answers else None
        session.max_score = max_total
        session.status = "COMPLETED" if len(answers) == len(questions) else "IN_PROGRESS"
        session.updated_by = actor_id
        session.updated_ip = request_ip
        self.db.flush()
        return session

    def count_session_answers(self, session_id: int) -> int:
        stmt = (
            select(func.count(ResumeInterviewAnswer.answer_id))
            .join(
                ResumeInterviewQuestion,
                ResumeInterviewQuestion.question_id
                == ResumeInterviewAnswer.question_id,
            )
            .where(ResumeInterviewQuestion.session_id == session_id)
        )
        return int(self.db.execute(stmt).scalar_one())
