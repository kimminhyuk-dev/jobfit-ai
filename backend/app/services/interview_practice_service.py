"""Business logic for OpenAI-based interview practice."""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.resume_interview import (
    ResumeInterviewAnswer,
    ResumeInterviewQuestion,
    ResumeInterviewSession,
)
from app.prompts.interview_references import (
    ALLOWED_REFERENCES_BY_URL,
    ALLOWED_REFERENCE_URLS,
    all_reference_materials,
)
from app.prompts.resume_interview import (
    INTERVIEW_QUESTION_COUNT,
    build_answer_evaluation_prompt,
    build_question_generation_prompt,
)
from app.repositories.interview_practice_repository import (
    InterviewPracticeRepository,
)
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume_interview import (
    InterviewAnswerResponse,
    InterviewQuestionResponse,
    InterviewReference,
    InterviewReferenceUsed,
    InterviewSessionCreateResponse,
    InterviewSessionDetailResponse,
)
from app.services.llm.openai_client import (
    OpenAIClient,
    OpenAIClientError,
    OpenAINotConfiguredError,
)
from app.services.resume_service import ResumeNotFoundError, ResumeService


class InterviewPracticeInvalidResumeError(Exception):
    """Resume is not ready for interview practice."""


class InterviewPracticeProviderNotConfiguredError(Exception):
    """OpenAI provider is not configured."""


class InterviewPracticeGenerationError(Exception):
    """Question generation failed."""


class InterviewPracticeEvaluationError(Exception):
    """Answer evaluation failed."""


class InterviewPracticeSessionNotFoundError(Exception):
    """Interview practice session was not found for this user/resume."""


class InterviewPracticeQuestionNotFoundError(Exception):
    """Interview practice question was not found for this user/resume."""


class InterviewPracticeService:
    """OpenAI-based interview practice workflow."""

    def __init__(self, db: Session, openai_client: OpenAIClient | None = None):
        self.db = db
        self.resume_service = ResumeService(db)
        self.resume_repository = ResumeRepository(db)
        self.repository = InterviewPracticeRepository(db)
        self.openai_client = openai_client or OpenAIClient()

    def create_session(
        self,
        *,
        resume_id: int,
        user_id: int,
        request_ip: str | None,
    ) -> InterviewSessionCreateResponse:
        resume = self._get_ready_resume(resume_id, user_id)
        projects, cover_letter_sections = self._get_resume_context(resume.resume_id)
        prompt = build_question_generation_prompt(
            parsed_data=resume.parsed_data,
            projects=projects,
            cover_letter_sections=cover_letter_sections,
            reference_materials=all_reference_materials(),
        )

        try:
            payload = self.openai_client.generate_interview_questions(prompt)
            questions_payload = _normalize_questions(payload)
        except OpenAINotConfiguredError as exc:
            raise InterviewPracticeProviderNotConfiguredError from exc
        except OpenAIClientError as exc:
            raise InterviewPracticeGenerationError from exc

        max_score = sum(item["max_score"] for item in questions_payload)
        try:
            session = self.repository.create_session(
                user_id=user_id,
                resume_id=resume.resume_id,
                model=self.openai_client.model_name,
                max_score=max_score,
                actor_id=user_id,
                request_ip=request_ip,
            )
            questions = self.repository.create_questions(
                session_id=session.session_id,
                questions=questions_payload,
                actor_id=user_id,
                request_ip=request_ip,
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        self.db.refresh(session)
        for question in questions:
            self.db.refresh(question)
        return self._build_session_response(session, questions, {})

    def get_session(
        self,
        *,
        resume_id: int,
        session_id: int,
        user_id: int,
    ) -> InterviewSessionDetailResponse:
        self.resume_service.get_resume(resume_id, user_id)
        session = self.repository.get_session_for_user(
            session_id=session_id,
            resume_id=resume_id,
            user_id=user_id,
        )
        if session is None:
            raise InterviewPracticeSessionNotFoundError
        questions = self.repository.list_questions(session.session_id)
        answers = self.repository.list_answers_by_question_ids(
            [question.question_id for question in questions]
        )
        return InterviewSessionDetailResponse(
            **self._build_session_response(session, questions, answers).model_dump()
        )

    def submit_answer(
        self,
        *,
        resume_id: int,
        question_id: int,
        user_id: int,
        answer: str,
        request_ip: str | None,
    ) -> InterviewAnswerResponse:
        resume = self.resume_service.get_resume(resume_id, user_id)
        question = self.repository.get_question_for_user(
            question_id=question_id,
            resume_id=resume_id,
            user_id=user_id,
        )
        if question is None:
            raise InterviewPracticeQuestionNotFoundError

        prompt = build_answer_evaluation_prompt(
            question=_question_to_prompt_dict(question),
            expected_keywords=question.expected_keywords or [],
            official_references=question.official_references or [],
            user_answer=answer,
            resume_context=_resume_context_for_evaluation(resume),
        )

        try:
            payload = self.openai_client.evaluate_interview_answer(prompt)
            evaluation = _normalize_evaluation(payload, question.max_score)
        except OpenAINotConfiguredError as exc:
            raise InterviewPracticeProviderNotConfiguredError from exc
        except OpenAIClientError as exc:
            raise InterviewPracticeEvaluationError from exc

        try:
            saved = self.repository.save_answer(
                question_id=question.question_id,
                user_answer=answer,
                score=evaluation["score"],
                max_score=evaluation["max_score"],
                verdict=evaluation["verdict"],
                strengths=evaluation["strengths"],
                missing_points=evaluation["missing_points"],
                incorrect_points=evaluation["incorrect_points"],
                feedback=evaluation["feedback"],
                reference_based_answer=evaluation["reference_based_answer"],
                official_references_used=evaluation["official_references_used"],
                model=self.openai_client.model_name,
                actor_id=user_id,
                request_ip=request_ip,
            )
            self.repository.update_session_score(
                session_id=question.session_id,
                actor_id=user_id,
                request_ip=request_ip,
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        self.db.refresh(saved)
        return _answer_to_response(saved)

    def _get_ready_resume(self, resume_id: int, user_id: int) -> Resume:
        resume = self.resume_service.get_resume(resume_id, user_id)
        if resume.parse_status != "COMPLETED" or not resume.parsed_data:
            raise InterviewPracticeInvalidResumeError
        return resume

    def _get_resume_context(
        self,
        resume_id: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        projects = [
            {
                "name": project.name,
                "period": project.period,
                "role": project.role,
                "description": project.description,
                "review": project.review,
                "tech_stack": project.tech_stack or [],
                "raw_text": project.raw_text,
            }
            for project in self.resume_repository.get_projects(resume_id)
        ]
        sections = [
            {
                "title": section.title,
                "content": section.content,
            }
            for section in self.resume_repository.get_cover_letter_sections(resume_id)
        ]
        return projects, sections

    def _build_session_response(
        self,
        session: ResumeInterviewSession,
        questions: list[ResumeInterviewQuestion],
        answers: dict[int, ResumeInterviewAnswer],
    ) -> InterviewSessionCreateResponse:
        return InterviewSessionCreateResponse(
            session_id=session.session_id,
            resume_id=session.resume_id,
            status=session.status,  # type: ignore[arg-type]
            model=session.model,
            total_score=session.total_score,
            max_score=session.max_score,
            questions=[
                _question_to_response(question, answers.get(question.question_id))
                for question in questions
            ],
        )


def _normalize_questions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list):
        raise InterviewPracticeGenerationError

    normalized: list[dict[str, Any]] = []
    for idx, raw in enumerate(raw_questions[:INTERVIEW_QUESTION_COUNT], start=1):
        if not isinstance(raw, dict):
            continue
        refs = _filter_official_references(raw.get("official_references") or [])
        normalized.append(
            {
                "display_order": _as_int(raw.get("display_order"), idx, 1, 5),
                "question": str(raw.get("question") or "").strip(),
                "question_type": _allowed_value(
                    raw.get("question_type"),
                    {"PROJECT", "TECH_STACK", "EXPERIENCE", "COVER_LETTER", "JOB_FIT"},
                    "PROJECT",
                ),
                "source": _allowed_value(
                    raw.get("source"),
                    {"parsed_data", "project", "cover_letter", "tech_stack", "experience"},
                    "parsed_data",
                ),
                "intent": str(raw.get("intent") or "").strip(),
                "difficulty": str(raw.get("difficulty") or "BASIC").strip() or "BASIC",
                "expected_keywords": _string_list(raw.get("expected_keywords")),
                "official_references": refs,
                "max_score": 20,
            }
        )

    normalized = [item for item in normalized if item["question"] and item["intent"]]
    if len(normalized) != INTERVIEW_QUESTION_COUNT:
        raise InterviewPracticeGenerationError
    normalized.sort(key=lambda item: item["display_order"])
    for idx, item in enumerate(normalized, start=1):
        item["display_order"] = idx
    return normalized


def _normalize_evaluation(
    payload: dict[str, Any],
    question_max_score: int,
) -> dict[str, Any]:
    score = _as_int(payload.get("score"), 0, 0, question_max_score)
    max_score = _as_int(payload.get("max_score"), question_max_score, 1, question_max_score)
    strengths = _string_list(payload.get("strengths"), limit=2, max_chars=120)
    missing_points = _string_list(payload.get("missing_points"), limit=2, max_chars=120)
    correct_points = _string_list(payload.get("correct_points"), limit=1, max_chars=120)
    different_points = _string_list(payload.get("different_points"), limit=1, max_chars=120)
    incorrect_points = _string_list(payload.get("incorrect_points"), limit=1, max_chars=120)
    if not correct_points and strengths:
        correct_points = strengths[:1]
    if not different_points and incorrect_points:
        different_points = incorrect_points[:1]
    return {
        "score": min(score, max_score),
        "max_score": max_score,
        "verdict": _allowed_value(
            payload.get("verdict"),
            {"GOOD", "PARTIAL", "INSUFFICIENT", "UNKNOWN"},
            "UNKNOWN",
        ),
        "strengths": strengths,
        "missing_points": missing_points,
        "incorrect_points": different_points or incorrect_points,
        "correct_points": correct_points,
        "different_points": different_points,
        "feedback": _short_text(payload.get("feedback"), max_chars=160),
        "reference_based_answer": _short_text(
            payload.get("reference_based_answer"),
            max_chars=260,
        ),
        "official_references_used": _filter_references_used(
            payload.get("official_references_used") or []
        ),
    }


def _filter_official_references(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if url not in ALLOWED_REFERENCE_URLS:
            continue
        allowed = ALLOWED_REFERENCES_BY_URL[url]
        refs.append(
            {
                "title": allowed["title"],
                "url": allowed["url"],
                "summary": allowed.get("summary"),
            }
        )
    return refs


def _filter_references_used(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if url not in ALLOWED_REFERENCE_URLS:
            continue
        allowed = ALLOWED_REFERENCES_BY_URL[url]
        refs.append({"title": allowed["title"], "url": allowed["url"]})
    return refs


def _question_to_response(
    question: ResumeInterviewQuestion,
    answer: ResumeInterviewAnswer | None,
) -> InterviewQuestionResponse:
    return InterviewQuestionResponse(
        question_id=question.question_id,
        display_order=question.display_order,
        question=question.question,
        question_type=question.question_type,  # type: ignore[arg-type]
        source=question.source,  # type: ignore[arg-type]
        intent=question.intent,
        difficulty=question.difficulty,
        expected_keywords=question.expected_keywords or [],
        official_references=[
            InterviewReference(**ref)
            for ref in (question.official_references or [])
            if isinstance(ref, dict)
        ],
        max_score=question.max_score,
        answer=_answer_to_response(answer) if answer else None,
    )


def _answer_to_response(answer: ResumeInterviewAnswer) -> InterviewAnswerResponse:
    return InterviewAnswerResponse(
        answer_id=answer.answer_id,
        question_id=answer.question_id,
        user_answer=answer.user_answer,
        score=answer.score,
        max_score=answer.max_score,
        verdict=answer.verdict,  # type: ignore[arg-type]
        strengths=answer.strengths or [],
        missing_points=answer.missing_points or [],
        incorrect_points=answer.incorrect_points or [],
        correct_points=(answer.strengths or [])[:1],
        different_points=(answer.incorrect_points or [])[:1],
        feedback=answer.feedback,
        reference_based_answer=answer.reference_based_answer,
        official_references_used=[
            InterviewReferenceUsed(**ref)
            for ref in (answer.official_references_used or [])
            if isinstance(ref, dict)
        ],
        model=answer.model,
    )


def _question_to_prompt_dict(question: ResumeInterviewQuestion) -> dict[str, Any]:
    return {
        "question_id": question.question_id,
        "question": question.question,
        "question_type": question.question_type,
        "source": question.source,
        "intent": question.intent,
        "difficulty": question.difficulty,
        "max_score": question.max_score,
    }


def _resume_context_for_evaluation(resume: Resume) -> dict[str, Any] | None:
    if not resume.parsed_data:
        return None
    return {
        "profile": resume.parsed_data.get("profile"),
        "skills": resume.parsed_data.get("skills"),
        "experiences": resume.parsed_data.get("experiences"),
        "projects": resume.parsed_data.get("projects"),
        "cover_letter_sections": resume.parsed_data.get("cover_letter_sections"),
    }


def _string_list(
    value: Any,
    *,
    limit: int | None = None,
    max_chars: int | None = None,
) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [str(item).strip() for item in value if str(item).strip()]
    if max_chars is not None:
        items = [_truncate(item, max_chars) for item in items]
    if limit is not None:
        items = items[:limit]
    return items


def _short_text(value: Any, *, max_chars: int) -> str:
    return _truncate(str(value or "").strip(), max_chars)


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars].rstrip()}..."


def _as_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _allowed_value(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or "").strip()
    return text if text in allowed else default
