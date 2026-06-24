"""이력서 청크 재생성 서비스."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.resume_chunk import ResumeChunk
from app.repositories.resume_repository import ResumeRepository
from app.services.rag.chunking import split_resume_into_chunks
from app.services.rag.embedding import (
    EmbeddingGenerationError,
    EmbeddingNotConfiguredError,
    embed_texts,
)
from app.services.resume_service import ResumeNotFoundError


class ResumeChunkRebuildError(Exception):
    """이력서 청크 재생성 실패"""


def rebuild_resume_chunks(
    db: Session,
    resume_id: int,
    *,
    actor_id: int | None = None,
    request_ip: str | None = None,
) -> dict[str, Any]:
    """이력서 청크를 삭제 후 재생성하고 pgvector에 저장한다."""

    resume_repository = ResumeRepository(db)
    resume = resume_repository.get_by_id_no_user(resume_id)
    if resume is None:
        raise ResumeNotFoundError

    setattr(resume, "resume_projects", resume_repository.get_projects(resume_id))
    setattr(
        resume,
        "resume_cover_letter_sections",
        resume_repository.get_cover_letter_sections(resume_id),
    )

    chunks = split_resume_into_chunks(resume)
    by_section = dict(Counter(chunk["section"] for chunk in chunks))

    vectors: list[list[float]] = []
    if chunks:
        # 조회 트랜잭션을 끝낸 뒤 외부 OpenAI 호출을 수행한다.
        # 실패하면 기존 resume_chunks는 아직 건드리지 않은 상태로 보존된다.
        db.rollback()
        vectors = embed_texts([chunk["content"] for chunk in chunks])

    try:
        db.execute(delete(ResumeChunk).where(ResumeChunk.resume_id == resume_id))
        if chunks:
            rows = [
                ResumeChunk(
                    resume_id=resume_id,
                    section=chunk["section"],
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    embedding=vectors[index],
                    created_by=actor_id,
                    created_ip=request_ip,
                    updated_by=actor_id,
                    updated_ip=request_ip,
                    reg_user_id=actor_id,
                    reg_ip=request_ip,
                    mod_user_id=actor_id,
                    mod_ip=request_ip,
                )
                for index, chunk in enumerate(chunks)
            ]
            db.bulk_save_objects(rows)
        db.commit()
    except (EmbeddingNotConfiguredError, EmbeddingGenerationError):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise ResumeChunkRebuildError from exc

    return {
        "resume_id": resume_id,
        "total": len(chunks),
        "by_section": by_section,
    }
