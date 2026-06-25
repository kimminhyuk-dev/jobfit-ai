"""채팅형 모의면접 DB 접근 계층."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mock_interview import (
    MOCK_INTERVIEW_STAGE_COMPLETED,
    MOCK_INTERVIEW_STATUS_COMPLETED,
    MockInterviewSession,
    MockInterviewTurn,
)


class MockInterviewRepository:
    """모의면접 세션과 턴 저장을 담당한다."""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        *,
        user_id: int,
        resume_id: int,
        job_id: int,
        stage: str,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewSession:
        """모의면접 세션을 만든다."""

        session = MockInterviewSession(
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            stage=stage,
            question_count=0,
            created_by=actor_id,
            created_ip=request_ip,
            updated_by=actor_id,
            updated_ip=request_ip,
            reg_user_id=actor_id,
            reg_ip=request_ip,
            mod_user_id=actor_id,
            mod_ip=request_ip,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def create_turn(
        self,
        *,
        session_id: int,
        turn_index: int,
        stage: str,
        question: str,
        based_on_chunk: dict[str, Any] | None,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewTurn:
        """질문 턴을 저장한다."""

        turn = MockInterviewTurn(
            session_id=session_id,
            turn_index=turn_index,
            stage=stage,
            question=question,
            based_on_chunk=based_on_chunk,
            created_by=actor_id,
            created_ip=request_ip,
            updated_by=actor_id,
            updated_ip=request_ip,
            reg_user_id=actor_id,
            reg_ip=request_ip,
            mod_user_id=actor_id,
            mod_ip=request_ip,
        )
        self.db.add(turn)
        self.db.flush()
        return turn

    def get_session_for_user(
        self,
        *,
        session_id: int,
        user_id: int,
    ) -> MockInterviewSession | None:
        """본인 소유 모의면접 세션을 조회한다."""

        stmt = (
            select(MockInterviewSession)
            .where(MockInterviewSession.session_id == session_id)
            .where(MockInterviewSession.user_id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_turns(self, session_id: int) -> list[MockInterviewTurn]:
        """세션의 턴을 순서대로 반환한다."""

        stmt = (
            select(MockInterviewTurn)
            .where(MockInterviewTurn.session_id == session_id)
            .order_by(MockInterviewTurn.turn_index)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_current_turn(self, session_id: int) -> MockInterviewTurn | None:
        """아직 답변하지 않은 최신 질문을 조회한다."""

        stmt = (
            select(MockInterviewTurn)
            .where(MockInterviewTurn.session_id == session_id)
            .where(MockInterviewTurn.user_answer.is_(None))
            .order_by(MockInterviewTurn.turn_index.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def save_answer(
        self,
        turn: MockInterviewTurn,
        *,
        answer: str,
        feedback: str,
        score: int,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewTurn:
        """답변과 짧은 피드백, 내부 점수를 저장한다."""

        turn.user_answer = answer
        turn.feedback = feedback
        turn.score = score
        turn.updated_by = actor_id
        turn.updated_ip = request_ip
        turn.mod_user_id = actor_id
        turn.mod_ip = request_ip
        self.db.flush()
        return turn

    def update_progress(
        self,
        session: MockInterviewSession,
        *,
        stage: str,
        question_count: int,
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewSession:
        """현재 단계와 질문 수를 갱신한다."""

        session.stage = stage
        session.question_count = question_count
        session.updated_by = actor_id
        session.updated_ip = request_ip
        session.mod_user_id = actor_id
        session.mod_ip = request_ip
        self.db.flush()
        return session

    def complete_session(
        self,
        session: MockInterviewSession,
        *,
        total_score: int,
        summary: dict[str, Any],
        actor_id: int,
        request_ip: str | None,
    ) -> MockInterviewSession:
        """세션을 종료하고 종합 리포트를 저장한다."""

        session.status = MOCK_INTERVIEW_STATUS_COMPLETED
        session.stage = MOCK_INTERVIEW_STAGE_COMPLETED
        session.total_score = total_score
        session.summary = summary
        session.completed_at = datetime.now(timezone.utc)
        session.updated_by = actor_id
        session.updated_ip = request_ip
        session.mod_user_id = actor_id
        session.mod_ip = request_ip
        self.db.flush()
        return session
