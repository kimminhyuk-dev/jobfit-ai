"""채팅형 모의면접 요청과 응답 스키마."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MockInterviewStatus = Literal["IN_PROGRESS", "COMPLETED", "ABANDONED"]
MockInterviewStage = Literal["WARMUP", "EXPERIENCE", "DEEP", "COMPLETED"]


class MockInterviewStartRequest(BaseModel):
    """모의면접 시작 요청."""

    resume_id: int = Field(..., gt=0)
    job_id: int | None = Field(default=None, gt=0)


class MockInterviewAnswerRequest(BaseModel):
    """모의면접 답변 제출 요청."""

    answer: str = Field(..., min_length=1, max_length=4000)


class MockInterviewReport(BaseModel):
    """종료 후 보여줄 종합 리포트."""

    total_score: int = Field(..., ge=0, le=100)
    summary: str = Field(..., min_length=1, max_length=800)
    strengths: list[str] = Field(default_factory=list, max_length=4)
    improvements: list[str] = Field(default_factory=list, max_length=4)
    next_steps: list[str] = Field(default_factory=list, max_length=4)


class MockInterviewTurnResponse(BaseModel):
    """모의면접 한 턴 응답."""

    turn_id: int
    turn_index: int
    stage: MockInterviewStage
    question: str
    user_answer: str | None
    feedback: str | None


class MockInterviewSessionResponse(BaseModel):
    """모의면접 세션 응답."""

    session_id: int
    resume_id: int
    job_id: int
    status: MockInterviewStatus
    stage: MockInterviewStage
    question_count: int
    total_score: int | None
    summary: MockInterviewReport | None
    created_at: str
    completed_at: str | None
    turns: list[MockInterviewTurnResponse]


class MockInterviewStartResponse(BaseModel):
    """모의면접 시작 응답."""

    session: MockInterviewSessionResponse
    current_turn: MockInterviewTurnResponse


class MockInterviewAnswerResponse(BaseModel):
    """답변 저장과 다음 질문 생성 응답."""

    session: MockInterviewSessionResponse
    answered_turn: MockInterviewTurnResponse
    next_turn: MockInterviewTurnResponse | None
    ready_to_finish: bool


class MockInterviewFinishResponse(BaseModel):
    """모의면접 종료 응답."""

    session: MockInterviewSessionResponse
    report: MockInterviewReport
