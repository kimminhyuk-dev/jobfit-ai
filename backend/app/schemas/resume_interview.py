"""이력서 면접 연습(OpenAI) 응답/요청 스키마."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

InterviewQuestionType = Literal[
    "PROJECT",
    "TECH_STACK",
    "EXPERIENCE",
    "COVER_LETTER",
    "JOB_FIT",
]

InterviewQuestionSource = Literal[
    "parsed_data",
    "project",
    "cover_letter",
    "tech_stack",
    "experience",
]

InterviewVerdict = Literal["GOOD", "PARTIAL", "INSUFFICIENT", "UNKNOWN"]

InterviewSessionStatus = Literal["IN_PROGRESS", "COMPLETED"]


class InterviewReference(BaseModel):
    """공식 근거 자료 한 건."""

    title: str
    url: str
    summary: str | None = None


class InterviewReferenceUsed(BaseModel):
    """채점에 실제로 사용된 공식 근거."""

    title: str
    url: str


class InterviewAnswerRequest(BaseModel):
    """답변 제출 요청. 비용 방지를 위해 길이를 제한한다."""

    answer: str = Field(..., min_length=1, max_length=5000)


class InterviewAnswerResponse(BaseModel):
    """채점 결과."""

    model_config = ConfigDict(from_attributes=True)

    answer_id: int
    question_id: int
    user_answer: str
    score: int
    max_score: int
    verdict: InterviewVerdict
    strengths: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    incorrect_points: list[str] = Field(default_factory=list)
    correct_points: list[str] = Field(default_factory=list)
    different_points: list[str] = Field(default_factory=list)
    feedback: str
    reference_based_answer: str
    official_references_used: list[InterviewReferenceUsed] = Field(default_factory=list)
    model: str


class InterviewQuestionResponse(BaseModel):
    """질문 + (있다면) 채점된 답변."""

    model_config = ConfigDict(from_attributes=True)

    question_id: int
    display_order: int
    question: str
    question_type: InterviewQuestionType
    source: InterviewQuestionSource
    intent: str
    difficulty: str
    expected_keywords: list[str] = Field(default_factory=list)
    official_references: list[InterviewReference] = Field(default_factory=list)
    max_score: int
    answer: InterviewAnswerResponse | None = None


class InterviewSessionCreateResponse(BaseModel):
    """세션 생성 + 질문 5개 생성 응답."""

    session_id: int
    resume_id: int
    status: InterviewSessionStatus
    model: str
    total_score: int | None = None
    max_score: int
    questions: list[InterviewQuestionResponse]


class InterviewSessionDetailResponse(InterviewSessionCreateResponse):
    """세션 조회 응답 (생성 응답과 동일 구조, 답변 포함)."""
