"""공고 요구사항 기반 이력서 청크 검색 서비스."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_posting import JobPosting
from app.models.resume_chunk import ResumeChunk
from app.services.rag.embedding import embed_texts


QUERY_PREVIEW_CHARS = 200
MAX_QUERY_TEXT_CHARS = 4000
REQUIREMENT_KEYWORDS = (
    "자격",
    "요건",
    "우대",
    "필수",
    "기술",
    "스킬",
    "역량",
    "경험",
    "담당",
    "직무",
    "업무",
)


def build_job_query_text(job_posting: JobPosting) -> str:
    """공고의 요구 기술/요구사항을 검색용 쿼리 문자열로 합친다."""

    parts: list[str] = []
    parts.extend(_flatten_text(job_posting.parsed_skills))
    parts.extend(
        _clean_part(part)
        for part in [
            job_posting.title,
            job_posting.career_level,
            job_posting.education,
            job_posting.employment_type,
            job_posting.ncs_category,
        ]
    )
    parts.extend(_requirement_lines(job_posting.raw_content))
    return _join_query_parts(parts)


def retrieve_resume_chunks(
    db: Session,
    resume_id: int,
    query_text: str,
    top_k: int = 5,
    sections: list[str] | None = None,
) -> list[dict[str, Any]]:
    """공고 쿼리와 가까운 해당 이력서의 chunk를 코사인 거리순으로 반환한다."""

    normalized_query = _clean_part(query_text)
    if not normalized_query:
        return []

    query_vector = embed_texts([normalized_query])[0]
    distance = ResumeChunk.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(
            ResumeChunk.id,
            ResumeChunk.section,
            ResumeChunk.content,
            distance,
        )
        .where(ResumeChunk.resume_id == resume_id)
        .order_by(distance)
        .limit(top_k)
    )
    clean_sections = _clean_sections(sections)
    if clean_sections:
        stmt = stmt.where(ResumeChunk.section.in_(clean_sections))

    rows = db.execute(stmt).all()
    return [
        {
            "chunk_id": row.id,
            "section": row.section,
            "content": row.content,
            "distance": float(row.distance),
            "similarity": 1 - float(row.distance),
        }
        for row in rows
    ]


def query_preview(query_text: str) -> str:
    """응답에 표시할 쿼리 미리보기 문자열을 만든다."""

    text = _clean_part(query_text)
    if len(text) <= QUERY_PREVIEW_CHARS:
        return text
    return f"{text[:QUERY_PREVIEW_CHARS].rstrip()}..."


def _requirement_lines(raw_content: str | None) -> list[str]:
    if not raw_content:
        return []
    lines = [
        _clean_part(line)
        for line in raw_content.splitlines()
        if _clean_part(line)
    ]
    matched = [
        line
        for line in lines
        if any(keyword in line for keyword in REQUIREMENT_KEYWORDS)
    ]
    return matched or lines[:20]


def _flatten_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = _clean_part(value)
        return [text] if text else []
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_flatten_text(item))
        return result
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            result.extend(_flatten_text(item))
        return result
    text = _clean_part(str(value))
    return [text] if text else []


def _join_query_parts(parts: list[str]) -> str:
    ordered: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = _clean_part(part)
        if not text or text in seen:
            continue
        ordered.append(text)
        seen.add(text)
    return "\n".join(ordered)[:MAX_QUERY_TEXT_CHARS].strip()


def _clean_sections(sections: list[str] | None) -> list[str]:
    if not sections:
        return []
    ordered: list[str] = []
    seen: set[str] = set()
    for section in sections:
        text = _clean_part(section)
        if text and text not in seen:
            ordered.append(text)
            seen.add(text)
    return ordered


def _clean_part(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()
