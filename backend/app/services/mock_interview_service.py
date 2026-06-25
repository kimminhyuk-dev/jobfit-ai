"""RAG 기반 채팅형 모의면접 서비스."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job_posting import JobPosting
from app.models.mock_interview import (
    MOCK_INTERVIEW_STAGE_DEEP,
    MOCK_INTERVIEW_STAGE_EXPERIENCE,
    MOCK_INTERVIEW_STAGE_WARMUP,
    MOCK_INTERVIEW_STATUS_COMPLETED,
    MOCK_INTERVIEW_STATUS_IN_PROGRESS,
    MockInterviewSession,
    MockInterviewTurn,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.repositories.mock_interview_repository import MockInterviewRepository
from app.schemas.mock_interview import (
    MockInterviewAnswerResponse,
    MockInterviewFinishResponse,
    MockInterviewReport,
    MockInterviewSessionResponse,
    MockInterviewStartResponse,
    MockInterviewTurnResponse,
)
from app.services.rag.embedding import (
    EmbeddingGenerationError,
    EmbeddingNotConfiguredError,
)
from app.services.rag.resume_chunk_service import (
    ResumeChunkRebuildError,
    rebuild_resume_chunks,
)
from app.services.rag.retrieval import build_job_query_text, retrieve_resume_chunks
from app.services.resume_service import ResumeNotFoundError, ResumeService


MAX_QUESTIONS = 6
RETRIEVAL_TOP_K = 7
JOB_CONTEXT_CHARS = 4500
CHUNK_CONTENT_CHARS = 650
MAX_GENERATION_TOKENS = 1300
MAX_REPORT_TOKENS = 1400

logger = logging.getLogger(__name__)


class MockInterviewInvalidResumeError(Exception):
    """모의면접에 사용할 수 있는 이력서가 아님."""


class MockInterviewNoJobError(Exception):
    """이력서에 연결된 지원 공고가 없음."""


class MockInterviewJobNotFoundError(Exception):
    """모의면접에 사용할 공고를 찾을 수 없음."""


class MockInterviewSessionNotFoundError(Exception):
    """모의면접 세션을 찾을 수 없음."""


class MockInterviewInvalidStateError(Exception):
    """모의면접 진행 상태가 올바르지 않음."""


class MockInterviewProviderNotConfiguredError(Exception):
    """OpenAI 설정이 없음."""


class MockInterviewGenerationError(Exception):
    """모의면접 질문이나 피드백 생성 실패."""


class _QuestionOutput(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    based_on_resume: str = Field(..., min_length=1, max_length=500)
    related_to_job: str = Field(..., min_length=1, max_length=500)


class _AnswerStepOutput(BaseModel):
    feedback: str = Field(..., min_length=1, max_length=500)
    score: int = Field(..., ge=0, le=100)
    next_question: str | None = Field(default=None, max_length=500)
    based_on_resume: str | None = Field(default=None, max_length=500)
    related_to_job: str | None = Field(default=None, max_length=500)


class MockInterviewService:
    """공고와 이력서 근거로 한 문제씩 모의면접을 진행한다."""

    def __init__(self, db: Session):
        self.db = db
        self.resume_service = ResumeService(db)
        self.application_repository = ApplicationRepository(db)
        self.job_posting_repository = JobPostingRepository(db)
        self.repository = MockInterviewRepository(db)

    def start(
        self,
        *,
        resume_id: int,
        user_id: int,
        job_id: int | None,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewStartResponse:
        """모의면접 세션을 만들고 첫 질문을 반환한다."""

        job, job_requirements, chunks = self._prepare_context(
            resume_id=resume_id,
            user_id=user_id,
            job_id=job_id,
            actor_id=actor_id,
            request_ip=request_ip,
        )
        output = self._generate_first_question(
            job=job,
            job_requirements=job_requirements,
            chunks=chunks,
        )
        stage = _stage_for_index(1)
        based_on_chunk = _based_on_chunk(output, chunks)

        try:
            session = self.repository.create_session(
                user_id=user_id,
                resume_id=resume_id,
                job_id=job.job_id,
                stage=stage,
                actor_id=actor_id,
                request_ip=request_ip,
            )
            turn = self.repository.create_turn(
                session_id=session.session_id,
                turn_index=1,
                stage=stage,
                question=output.question,
                based_on_chunk=based_on_chunk,
                actor_id=actor_id,
                request_ip=request_ip,
            )
            self.repository.update_progress(
                session,
                stage=stage,
                question_count=1,
                actor_id=actor_id,
                request_ip=request_ip,
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        self.db.refresh(session)
        self.db.refresh(turn)
        session_response = self._session_response(session, [turn])
        return MockInterviewStartResponse(
            session=session_response,
            current_turn=_turn_response(turn),
        )

    def answer(
        self,
        *,
        session_id: int,
        user_id: int,
        answer: str,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewAnswerResponse:
        """현재 질문 답변을 저장하고 다음 질문을 만든다."""

        session = self._get_session(session_id, user_id)
        self._ensure_in_progress(session)
        turn = self.repository.get_current_turn(session.session_id)
        if turn is None:
            raise MockInterviewInvalidStateError

        job, job_requirements, chunks = self._prepare_context(
            resume_id=session.resume_id,
            user_id=user_id,
            job_id=session.job_id,
            actor_id=actor_id,
            request_ip=request_ip,
        )
        next_index = turn.turn_index + 1
        has_next = next_index <= MAX_QUESTIONS
        output = self._evaluate_answer_and_next(
            job=job,
            job_requirements=job_requirements,
            chunks=chunks,
            turn=turn,
            answer=answer,
            next_index=next_index,
            has_next=has_next,
        )
        if has_next and not output.next_question:
            raise MockInterviewGenerationError

        try:
            answered_turn = self.repository.save_answer(
                turn,
                answer=answer,
                feedback=output.feedback,
                score=output.score,
                actor_id=actor_id,
                request_ip=request_ip,
            )
            next_turn = None
            if has_next and output.next_question:
                next_stage = _stage_for_index(next_index)
                next_turn = self.repository.create_turn(
                    session_id=session.session_id,
                    turn_index=next_index,
                    stage=next_stage,
                    question=output.next_question,
                    based_on_chunk=_based_on_chunk(output, chunks),
                    actor_id=actor_id,
                    request_ip=request_ip,
                )
                self.repository.update_progress(
                    session,
                    stage=next_stage,
                    question_count=next_index,
                    actor_id=actor_id,
                    request_ip=request_ip,
                )
            else:
                self.repository.update_progress(
                    session,
                    stage=turn.stage,
                    question_count=session.question_count,
                    actor_id=actor_id,
                    request_ip=request_ip,
                )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        self.db.refresh(session)
        self.db.refresh(answered_turn)
        if next_turn:
            self.db.refresh(next_turn)
        turns = self.repository.list_turns(session.session_id)
        return MockInterviewAnswerResponse(
            session=self._session_response(session, turns),
            answered_turn=_turn_response(answered_turn),
            next_turn=_turn_response(next_turn) if next_turn else None,
            ready_to_finish=not has_next,
        )

    def finish(
        self,
        *,
        session_id: int,
        user_id: int,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewFinishResponse:
        """모의면접을 종료하고 종합 리포트를 만든다."""

        session = self._get_session(session_id, user_id)
        if session.status == MOCK_INTERVIEW_STATUS_COMPLETED:
            turns = self.repository.list_turns(session.session_id)
            report = _report_from_summary(session.summary, session.total_score)
            return MockInterviewFinishResponse(
                session=self._session_response(session, turns),
                report=report,
            )
        self._ensure_in_progress(session)
        turns = self.repository.list_turns(session.session_id)
        if not turns or any(turn.user_answer is None for turn in turns):
            raise MockInterviewInvalidStateError

        job = self.job_posting_repository.get_by_id(session.job_id)
        if job is None:
            raise MockInterviewJobNotFoundError
        report = self._generate_report(job=job, turns=turns)

        try:
            self.repository.complete_session(
                session,
                total_score=report.total_score,
                summary=report.model_dump(mode="json"),
                actor_id=actor_id,
                request_ip=request_ip,
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        self.db.refresh(session)
        turns = self.repository.list_turns(session.session_id)
        return MockInterviewFinishResponse(
            session=self._session_response(session, turns),
            report=report,
        )

    def get_session(
        self,
        *,
        session_id: int,
        user_id: int,
    ) -> MockInterviewSessionResponse:
        """모의면접 세션과 대화를 조회한다."""

        session = self._get_session(session_id, user_id)
        turns = self.repository.list_turns(session.session_id)
        return self._session_response(session, turns)

    def _prepare_context(
        self,
        *,
        resume_id: int,
        user_id: int,
        job_id: int | None,
        actor_id: int,
        request_ip: str | None,
    ) -> tuple[JobPosting, str, list[dict[str, Any]]]:
        resume = self.resume_service.get_resume(resume_id, user_id)
        if resume.parse_status != "COMPLETED" or not (
            resume.raw_text or resume.parsed_data
        ):
            raise MockInterviewInvalidResumeError

        job = self._resolve_job(
            resume_id=resume_id,
            user_id=user_id,
            job_id=job_id,
        )
        job_requirements = build_job_query_text(job)
        if not job_requirements.strip():
            raise MockInterviewJobNotFoundError

        try:
            rebuild_resume_chunks(
                self.db,
                resume_id,
                actor_id=actor_id,
                request_ip=request_ip,
                skip_if_unchanged=True,
            )
            chunks = retrieve_resume_chunks(
                self.db,
                resume_id,
                job_requirements,
                top_k=RETRIEVAL_TOP_K,
            )
        except EmbeddingNotConfiguredError as exc:
            raise MockInterviewProviderNotConfiguredError from exc
        except (EmbeddingGenerationError, ResumeChunkRebuildError) as exc:
            raise MockInterviewGenerationError from exc

        if not chunks:
            raise MockInterviewInvalidResumeError
        return job, job_requirements, chunks

    def _resolve_job(
        self,
        *,
        resume_id: int,
        user_id: int,
        job_id: int | None,
    ) -> JobPosting:
        if job_id is None:
            application = self.application_repository.get_latest_active_by_resume_for_user(
                resume_id=resume_id,
                user_id=user_id,
            )
            if application is None:
                raise MockInterviewNoJobError
            job = self.job_posting_repository.get_by_id(application.job_id)
            if job is None:
                raise MockInterviewJobNotFoundError
            return job

        application = self.application_repository.get_active_by_resume_job_for_user(
            resume_id=resume_id,
            job_id=job_id,
            user_id=user_id,
        )
        job = self.job_posting_repository.get_by_id(job_id)
        if job is None:
            raise MockInterviewJobNotFoundError
        if job.status == "HIDDEN" and application is None:
            raise MockInterviewJobNotFoundError
        return job

    def _generate_first_question(
        self,
        *,
        job: JobPosting,
        job_requirements: str,
        chunks: list[dict[str, Any]],
    ) -> _QuestionOutput:
        parser = PydanticOutputParser(pydantic_object=_QuestionOutput)
        prompt = PromptTemplate(
            template=_FIRST_QUESTION_PROMPT,
            input_variables=[
                "job_title",
                "company_name",
                "job_requirements",
                "resume_chunks",
            ],
            partial_variables={
                "format_instructions": parser.get_format_instructions()
            },
        )
        chain = prompt | _chat_model(MAX_GENERATION_TOKENS) | parser
        try:
            return chain.invoke(
                {
                    "job_title": job.title or "",
                    "company_name": job.company_name or "",
                    "job_requirements": _truncate(
                        job_requirements,
                        JOB_CONTEXT_CHARS,
                    ),
                    "resume_chunks": _compact(_chunk_prompt_items(chunks)),
                }
            )
        except MockInterviewProviderNotConfiguredError:
            raise
        except Exception as exc:
            logger.warning(
                "Mock interview first question failed: %s",
                exc.__class__.__name__,
            )
            raise MockInterviewGenerationError from exc

    def _evaluate_answer_and_next(
        self,
        *,
        job: JobPosting,
        job_requirements: str,
        chunks: list[dict[str, Any]],
        turn: MockInterviewTurn,
        answer: str,
        next_index: int,
        has_next: bool,
    ) -> _AnswerStepOutput:
        parser = PydanticOutputParser(pydantic_object=_AnswerStepOutput)
        prompt = PromptTemplate(
            template=_ANSWER_STEP_PROMPT,
            input_variables=[
                "job_title",
                "company_name",
                "job_requirements",
                "resume_chunks",
                "current_stage",
                "current_question",
                "user_answer",
                "next_index",
                "next_stage",
                "has_next",
            ],
            partial_variables={
                "format_instructions": parser.get_format_instructions()
            },
        )
        chain = prompt | _chat_model(MAX_GENERATION_TOKENS) | parser
        try:
            return chain.invoke(
                {
                    "job_title": job.title or "",
                    "company_name": job.company_name or "",
                    "job_requirements": _truncate(
                        job_requirements,
                        JOB_CONTEXT_CHARS,
                    ),
                    "resume_chunks": _compact(_chunk_prompt_items(chunks)),
                    "current_stage": turn.stage,
                    "current_question": turn.question,
                    "user_answer": _truncate(answer, 4000),
                    "next_index": next_index,
                    "next_stage": _stage_for_index(next_index) if has_next else "NONE",
                    "has_next": "true" if has_next else "false",
                }
            )
        except MockInterviewProviderNotConfiguredError:
            raise
        except Exception as exc:
            logger.warning(
                "Mock interview answer step failed: %s",
                exc.__class__.__name__,
            )
            raise MockInterviewGenerationError from exc

    def _generate_report(
        self,
        *,
        job: JobPosting,
        turns: list[MockInterviewTurn],
    ) -> MockInterviewReport:
        parser = PydanticOutputParser(pydantic_object=MockInterviewReport)
        prompt = PromptTemplate(
            template=_REPORT_PROMPT,
            input_variables=["job_title", "company_name", "turns"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()
            },
        )
        chain = prompt | _chat_model(MAX_REPORT_TOKENS) | parser
        try:
            return chain.invoke(
                {
                    "job_title": job.title or "",
                    "company_name": job.company_name or "",
                    "turns": _compact(_turn_prompt_items(turns)),
                }
            )
        except MockInterviewProviderNotConfiguredError:
            raise
        except Exception as exc:
            logger.warning(
                "Mock interview report failed: %s",
                exc.__class__.__name__,
            )
            raise MockInterviewGenerationError from exc

    def _get_session(
        self,
        session_id: int,
        user_id: int,
    ) -> MockInterviewSession:
        session = self.repository.get_session_for_user(
            session_id=session_id,
            user_id=user_id,
        )
        if session is None:
            raise MockInterviewSessionNotFoundError
        return session

    def _ensure_in_progress(self, session: MockInterviewSession) -> None:
        if session.status != MOCK_INTERVIEW_STATUS_IN_PROGRESS:
            raise MockInterviewInvalidStateError

    def _session_response(
        self,
        session: MockInterviewSession,
        turns: list[MockInterviewTurn],
    ) -> MockInterviewSessionResponse:
        return MockInterviewSessionResponse(
            session_id=session.session_id,
            resume_id=session.resume_id,
            job_id=session.job_id,
            status=session.status,  # type: ignore[arg-type]
            stage=session.stage,  # type: ignore[arg-type]
            question_count=session.question_count,
            total_score=session.total_score,
            summary=_report_from_summary(session.summary, session.total_score)
            if session.summary
            else None,
            created_at=session.created_at.isoformat(),
            completed_at=session.completed_at.isoformat()
            if session.completed_at
            else None,
            turns=[_turn_response(turn) for turn in turns],
        )


def _chat_model(max_tokens: int) -> ChatOpenAI:
    if not settings.openai_api_key:
        raise MockInterviewProviderNotConfiguredError
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        max_tokens=max_tokens,
        reasoning_effort=settings.openai_reasoning_effort,
    )


def _turn_response(turn: MockInterviewTurn) -> MockInterviewTurnResponse:
    return MockInterviewTurnResponse(
        turn_id=turn.turn_id,
        turn_index=turn.turn_index,
        stage=turn.stage,  # type: ignore[arg-type]
        question=turn.question,
        user_answer=turn.user_answer,
        feedback=turn.feedback,
    )


def _stage_for_index(index: int) -> str:
    if index <= 2:
        return MOCK_INTERVIEW_STAGE_WARMUP
    if index <= 4:
        return MOCK_INTERVIEW_STAGE_EXPERIENCE
    return MOCK_INTERVIEW_STAGE_DEEP


def _chunk_prompt_items(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks, start=1):
        items.append(
            {
                "order": index,
                "chunk_id": chunk["chunk_id"],
                "section": chunk["section"],
                "similarity": round(float(chunk["similarity"]), 4),
                "content": _truncate(chunk["content"], CHUNK_CONTENT_CHARS),
            }
        )
    return items


def _turn_prompt_items(turns: list[MockInterviewTurn]) -> list[dict[str, Any]]:
    return [
        {
            "turn_index": turn.turn_index,
            "stage": turn.stage,
            "question": turn.question,
            "answer": _truncate(turn.user_answer or "", 1200),
            "feedback": turn.feedback or "",
            "score": turn.score,
        }
        for turn in turns
    ]


def _based_on_chunk(
    output: _QuestionOutput | _AnswerStepOutput,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "based_on_resume": getattr(output, "based_on_resume", None),
        "related_to_job": getattr(output, "related_to_job", None),
        "chunks": _chunk_prompt_items(chunks),
    }


def _report_from_summary(
    summary: dict[str, Any] | None,
    total_score: int | None,
) -> MockInterviewReport:
    if isinstance(summary, dict):
        data = dict(summary)
        if total_score is not None:
            data["total_score"] = total_score
        return MockInterviewReport(**data)
    return MockInterviewReport(
        total_score=total_score or 0,
        summary="아직 종합 리포트가 없습니다.",
        strengths=[],
        improvements=[],
        next_steps=[],
    )


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _truncate(value: str, max_chars: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}..."


_FIRST_QUESTION_PROMPT = """당신은 실제 개발자 면접을 진행하는 면접관입니다.

아래 공고와 검색된 이력서 근거만 사용해 채팅형 모의면접의 1번 질문을 만드세요.

규칙:
- 한국어 존댓말 한 문장으로 씁니다.
- 1번 질문은 반드시 워밍업입니다.
- 지원 직무와 연결해 본인이 한 업무, 프로젝트, 사용 기술을 짧게 소개하게 묻습니다.
- 복잡한 설계, 보안, 성능 질문으로 시작하지 않습니다.
- 질문 안에 "워밍업", "경험", "심화" 같은 단계 이름은 쓰지 않습니다.
- 없는 프로젝트, 회사, 기술, 성과는 만들지 않습니다.
- JSON만 반환합니다.

[공고]
회사: {company_name}
공고명: {job_title}

[공고 요구사항]
{job_requirements}

[검색된 이력서 근거]
{resume_chunks}

{format_instructions}
"""


_ANSWER_STEP_PROMPT = """당신은 실제 개발자 면접을 진행하는 면접관입니다.

현재 질문에 대한 답변을 짧게 평가하고, 필요하면 다음 질문을 한 개 만드세요.

규칙:
- feedback은 2문장 이내로 씁니다. 먼저 잘한 점, 그다음 보완점을 말합니다.
- score는 내부 기록용 0~100 정수입니다.
- has_next가 false이면 next_question, based_on_resume, related_to_job은 null로 둡니다.
- has_next가 true이면 next_stage와 next_index에 맞는 다음 질문을 만듭니다.
- 1~2번 WARMUP: 자기소개, 직무 기초 개념을 묻습니다.
- next_index가 2이면 프로젝트 구현 세부보다 Java OOP, Spring 요청 흐름, REST API, SQL GROUP BY 같은 직무 기초 개념을 묻습니다.
- 3~4번 EXPERIENCE: 이력서 프로젝트에서 한 일, 기술 선택 이유, 문제 해결 방법을 묻습니다.
- 5~6번 DEEP: 공고 요구와 이력서 경험을 엮은 깊은 기술 질문이나 단점 극복 질문을 묻습니다.
- 다음 질문은 한국어 존댓말 한 문장입니다.
- 다음 질문 안에 "워밍업", "경험", "심화" 같은 단계 이름은 쓰지 않습니다.
- 모델명, 점수, RAG, chunk 같은 내부 단어는 질문이나 피드백에 쓰지 않습니다.
- 없는 프로젝트, 회사, 기술, 성과는 만들지 않습니다.
- JSON만 반환합니다.

[공고]
회사: {company_name}
공고명: {job_title}

[공고 요구사항]
{job_requirements}

[검색된 이력서 근거]
{resume_chunks}

[현재 단계]
{current_stage}

[현재 질문]
{current_question}

[지원자 답변]
{user_answer}

[다음 질문 조건]
has_next: {has_next}
next_index: {next_index}
next_stage: {next_stage}

{format_instructions}
"""


_REPORT_PROMPT = """당신은 개발자 모의면접 코치입니다.

아래 전체 질문, 답변, 피드백, 내부 점수를 바탕으로 최종 리포트를 만드세요.

규칙:
- total_score는 전체 답변 품질을 0~100 정수로 평가합니다.
- summary는 4문장 이내의 종합 총평입니다.
- strengths, improvements, next_steps는 각각 2~4개로 씁니다.
- 한국어 존댓말로 씁니다.
- 모델명, RAG, chunk 같은 내부 단어는 쓰지 않습니다.
- JSON만 반환합니다.

[공고]
회사: {company_name}
공고명: {job_title}

[면접 대화]
{turns}

{format_instructions}
"""
