"""공고와 이력서 RAG 근거를 교차한 면접질문 생성 서비스."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job_posting import JobPosting
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_posting_repository import JobPostingRepository
from app.schemas.job_interview import (
    JobBasedInterviewQuestionResponse,
    JobBasedInterviewQuestionSet,
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
from app.services.resume_service import ResumeService


RETRIEVAL_TOP_K = 7
JOB_CONTEXT_CHARS = 4500
CHUNK_CONTENT_CHARS = 650
MAX_OUTPUT_TOKENS = 1500

logger = logging.getLogger(__name__)


class JobBasedInterviewInvalidResumeError(Exception):
    """면접질문을 만들 수 있는 이력서가 아님."""


class JobBasedInterviewNoJobError(Exception):
    """이력서에 연결된 지원 공고가 없음."""


class JobBasedInterviewJobNotFoundError(Exception):
    """질문 생성에 사용할 공고를 찾을 수 없음."""


class JobBasedInterviewProviderNotConfiguredError(Exception):
    """OpenAI 설정이 없음."""


class JobBasedInterviewGenerationError(Exception):
    """공고 맞춤 면접질문 생성 실패."""


class JobBasedInterviewService:
    """공고 요구와 이력서 검색 근거를 조합해 면접질문을 만든다."""

    def __init__(self, db: Session):
        self.db = db
        self.resume_service = ResumeService(db)
        self.application_repository = ApplicationRepository(db)
        self.job_posting_repository = JobPostingRepository(db)

    def generate_questions(
        self,
        *,
        resume_id: int,
        user_id: int,
        job_id: int | None,
        actor_id: int,
        request_ip: str | None,
    ) -> JobBasedInterviewQuestionResponse:
        """본인 이력서와 공고 요구사항을 교차해 질문 5개를 생성한다."""

        resume = self.resume_service.get_resume(resume_id, user_id)
        if resume.parse_status != "COMPLETED" or not (
            resume.raw_text or resume.parsed_data
        ):
            raise JobBasedInterviewInvalidResumeError

        job = self._resolve_job(
            resume_id=resume_id,
            user_id=user_id,
            job_id=job_id,
        )
        job_requirements = build_job_query_text(job)
        if not job_requirements.strip():
            raise JobBasedInterviewJobNotFoundError

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
            raise JobBasedInterviewProviderNotConfiguredError from exc
        except (EmbeddingGenerationError, ResumeChunkRebuildError) as exc:
            raise JobBasedInterviewGenerationError from exc

        if not chunks:
            raise JobBasedInterviewInvalidResumeError

        output = self._run_chain(
            job=job,
            job_requirements=job_requirements,
            chunks=chunks,
        )
        return JobBasedInterviewQuestionResponse(
            resume_id=resume_id,
            job_id=job.job_id,
            job_title=job.title,
            company_name=job.company_name,
            model=settings.openai_model,
            chunk_count=len(chunks),
            questions=output.questions,
        )

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
                raise JobBasedInterviewNoJobError
            job = self.job_posting_repository.get_by_id(application.job_id)
            if job is None:
                raise JobBasedInterviewJobNotFoundError
            return job

        application = self.application_repository.get_active_by_resume_job_for_user(
            resume_id=resume_id,
            job_id=job_id,
            user_id=user_id,
        )
        job = self.job_posting_repository.get_by_id(job_id)
        if job is None:
            raise JobBasedInterviewJobNotFoundError
        if job.status == "HIDDEN" and application is None:
            raise JobBasedInterviewJobNotFoundError
        return job

    def _run_chain(
        self,
        *,
        job: JobPosting,
        job_requirements: str,
        chunks: list[dict[str, Any]],
    ) -> JobBasedInterviewQuestionSet:
        if not settings.openai_api_key:
            raise JobBasedInterviewProviderNotConfiguredError

        parser = PydanticOutputParser(
            pydantic_object=JobBasedInterviewQuestionSet
        )
        prompt = PromptTemplate(
            template=_PROMPT_TEMPLATE,
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
        model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            max_tokens=MAX_OUTPUT_TOKENS,
            reasoning_effort=settings.openai_reasoning_effort,
        )
        chain = prompt | model | parser

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
        except JobBasedInterviewProviderNotConfiguredError:
            raise
        except Exception as exc:
            logger.warning(
                "Job-based interview question generation failed: %s",
                exc.__class__.__name__,
            )
            raise JobBasedInterviewGenerationError from exc


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


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _truncate(value: str, max_chars: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}..."


_PROMPT_TEMPLATE = """당신은 신입 및 주니어 개발자 채용 면접관입니다.

아래 공고 요구사항과 검색된 이력서 근거만 사용해 공고 맞춤 면접질문을 정확히 5개 만드세요.

규칙:
- 모든 자연어는 한국어 존댓말로 씁니다.
- 질문은 실제 면접관이 말하듯 자연스럽게 한 문장으로 씁니다.
- 질문 배열은 실제 면접 순서처럼 쉬운 질문에서 깊은 질문으로 배치합니다.
- 1번은 워밍업입니다. 지원 직무와 연결해 본인 경험이나 프로젝트에서 어떤 업무를 했는지 소개하게 묻습니다.
- 2번은 기초 질문입니다. 백엔드 공고면 Java, Spring, REST API, 인증 같은 기초를 묻고, Python 직무면 Python 기초를 묻는 식으로 공고 직무에 맞춥니다.
- 3번과 4번은 경험 기반 질문입니다. 이력서 프로젝트에서 맡은 일, 기술 선택 이유, 구현 과정, 문제 해결을 묻습니다.
- 5번은 심화 질문입니다. 공고 요구사항과 이력서 경험을 엮어 설계, 보안, 성능, 확장성 중 가장 관련 깊은 주제를 묻습니다.
- 첫 질문부터 복잡한 설계, 보안, 성능 질문을 하지 않습니다.
- 질문 안에 "워밍업", "기초", "심화" 같은 단계 이름은 쓰지 않습니다.
- 질문마다 이력서 근거와 공고 연결점을 함께 씁니다.
- based_on_resume에는 이력서 chunk에 있는 프로젝트, 기술, 경험만 요약합니다.
- related_to_job에는 공고 요구사항 중 연결되는 기술이나 업무만 요약합니다.
- 없는 프로젝트, 회사, 기술, 성과, 수치, 자격은 만들지 않습니다.
- 점수나 합격 가능성은 쓰지 않습니다.
- 질문 1개는 180자 이내, 근거와 연결점은 각각 120자 이내로 씁니다.
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
