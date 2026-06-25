"""공고 맞춤 면접질문 요청과 응답 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JobBasedInterviewQuestionRequest(BaseModel):
    """공고 맞춤 면접질문 생성 요청."""

    job_id: int | None = Field(default=None, gt=0)


class JobBasedInterviewQuestionItem(BaseModel):
    """공고와 이력서 근거를 함께 담은 질문."""

    question: str = Field(..., min_length=1, max_length=500)
    based_on_resume: str = Field(..., min_length=1, max_length=500)
    related_to_job: str = Field(..., min_length=1, max_length=500)


class JobBasedInterviewQuestionSet(BaseModel):
    """LangChain 출력 파서가 검증하는 질문 묶음."""

    questions: list[JobBasedInterviewQuestionItem] = Field(
        ...,
        min_length=5,
        max_length=5,
    )


class JobBasedInterviewQuestionResponse(BaseModel):
    """공고 맞춤 면접질문 생성 응답."""

    resume_id: int
    job_id: int
    job_title: str | None
    company_name: str | None
    model: str
    chunk_count: int
    questions: list[JobBasedInterviewQuestionItem]
