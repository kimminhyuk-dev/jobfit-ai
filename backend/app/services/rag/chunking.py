"""이력서 텍스트를 RAG 검색용 섹션 청크로 분리한다."""

from __future__ import annotations

import json
import re
from typing import Any

from app.models.resume import Resume


MAX_CHUNK_CHARS = 500
OVERLAP_CHARS = 50

_BLANK_LINE_RE = re.compile(r"\n\s*\n+")
_SENTENCE_BOUNDARY_RE = re.compile(
    r"(?<=[.!?。！？])\s+|(?<=[다요죠함됨음])\s+(?=[가-힣A-Za-z0-9])"
)
_SPACE_RE = re.compile(r"[ \t]+")


def split_resume_into_chunks(resume: Resume) -> list[dict[str, Any]]:
    """이력서를 섹션 단위 chunk로 분리한다. 반환: [{section, chunk_index, content}, ...]"""

    section_texts = _collect_section_texts(resume)
    chunks: list[dict[str, Any]] = []
    seen_contents: set[str] = set()

    for section, content in section_texts:
        normalized = _normalize_text(content)
        if not normalized or normalized in seen_contents:
            continue
        seen_contents.add(normalized)

        for chunk_content in _split_section_content(normalized):
            chunks.append(
                {
                    "section": section,
                    "chunk_index": len(chunks),
                    "content": chunk_content,
                }
            )

    return chunks


def _collect_section_texts(resume: Resume) -> list[tuple[str, str]]:
    parsed = resume.parsed_data or {}
    sections: list[tuple[str, str]] = []

    sections.extend(_parsed_section_texts(parsed))
    sections.extend(_project_section_texts(resume, parsed))
    sections.extend(_cover_letter_section_texts(resume, parsed))

    return [
        (section, content)
        for section, content in sections
        if section and content and content.strip()
    ]


def _parsed_section_texts(parsed: dict[str, Any]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    fields = [
        ("기본정보", parsed.get("profile")),
        ("기술스택", parsed.get("skills")),
        ("학력", parsed.get("education")),
        ("교육", parsed.get("training")),
        ("경력", parsed.get("experiences")),
        ("자격증", parsed.get("certifications")),
        ("수상", parsed.get("awards")),
        ("어학", parsed.get("languages")),
        ("하이라이트", parsed.get("highlights")),
    ]
    for label, value in fields:
        text = _stringify_value(value)
        if text:
            result.append((label, text))

    raw_sections = parsed.get("sections")
    if isinstance(raw_sections, dict):
        for key, value in raw_sections.items():
            label = _section_label(str(key))
            text = _stringify_value(value)
            if text:
                result.append((label, text))
    return result


def _project_section_texts(
    resume: Resume,
    parsed: dict[str, Any],
) -> list[tuple[str, str]]:
    rows = list(getattr(resume, "resume_projects", None) or [])
    if rows:
        result = []
        for project in rows:
            parts = [
                project.name,
                project.period,
                project.role,
                project.description,
                project.review,
                _stringify_value(project.tech_stack),
                project.raw_text,
            ]
            text = _join_parts(parts)
            if text:
                result.append(("프로젝트", text))
        return result

    return [
        ("프로젝트", text)
        for text in _flatten_text(parsed.get("projects"))
        if text
    ]


def _cover_letter_section_texts(
    resume: Resume,
    parsed: dict[str, Any],
) -> list[tuple[str, str]]:
    rows = list(getattr(resume, "resume_cover_letter_sections", None) or [])
    if rows:
        return [
            ("자소서", _join_parts([section.title, section.content]))
            for section in rows
            if section.content and section.content.strip()
        ]

    raw_sections = parsed.get("cover_letter_sections")
    if isinstance(raw_sections, dict):
        result = []
        for title, content in raw_sections.items():
            text = _join_parts([str(title), _stringify_value(content)])
            if text:
                result.append(("자소서", text))
        return result

    cover_letter = _stringify_value(parsed.get("cover_letter"))
    return [("자소서", cover_letter)] if cover_letter else []


def _split_section_content(content: str) -> list[str]:
    if len(content) <= MAX_CHUNK_CHARS:
        return [content]

    units = _paragraph_and_sentence_units(content)
    return _pack_units(units)


def _paragraph_and_sentence_units(content: str) -> list[str]:
    units: list[str] = []
    for paragraph in _BLANK_LINE_RE.split(content):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= MAX_CHUNK_CHARS:
            units.append(paragraph)
            continue
        sentences = [
            sentence.strip()
            for sentence in _SENTENCE_BOUNDARY_RE.split(paragraph)
            if sentence and sentence.strip()
        ]
        if len(sentences) <= 1:
            units.extend(_slice_long_text(paragraph))
        else:
            for sentence in sentences:
                if len(sentence) <= MAX_CHUNK_CHARS:
                    units.append(sentence)
                else:
                    units.extend(_slice_long_text(sentence))
    return units


def _pack_units(units: list[str]) -> list[str]:
    chunks: list[str] = []
    current = ""

    for unit in units:
        if not unit:
            continue
        candidate = _join_parts([current, unit]) if current else unit
        if len(candidate) <= MAX_CHUNK_CHARS:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = _join_parts([_overlap_tail(current), unit])
        else:
            chunks.extend(_slice_long_text(unit))
            current = ""

        while len(current) > MAX_CHUNK_CHARS:
            chunks.append(current[:MAX_CHUNK_CHARS].strip())
            current = _join_parts([_overlap_tail(chunks[-1]), current[MAX_CHUNK_CHARS:]])

    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk]


def _slice_long_text(text: str) -> list[str]:
    chunks: list[str] = []
    step = MAX_CHUNK_CHARS - OVERLAP_CHARS
    start = 0
    while start < len(text):
        chunk = text[start:start + MAX_CHUNK_CHARS].strip()
        if chunk:
            chunks.append(chunk)
        if start + MAX_CHUNK_CHARS >= len(text):
            break
        start += step
    return chunks


def _overlap_tail(text: str) -> str:
    tail = text[-OVERLAP_CHARS:].strip()
    if not tail:
        return ""
    first_space = tail.find(" ")
    if first_space > 0:
        return tail[first_space + 1:].strip()
    return tail


def _section_label(value: str) -> str:
    mapping = {
        "profile": "기본정보",
        "skills": "기술스택",
        "education": "학력",
        "training": "교육",
        "experience": "경력",
        "experiences": "경력",
        "projects": "프로젝트",
        "certifications": "자격증",
        "cover_letter": "자소서",
        "awards": "수상",
        "languages": "어학",
    }
    return mapping.get(value, value[:80] or "기타")


def _stringify_value(value: Any) -> str:
    return _join_parts(_flatten_text(value))


def _flatten_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        result: list[str] = []
        for key, item in value.items():
            item_text = _stringify_value(item)
            if item_text:
                result.append(f"{key}: {item_text}")
        return result
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            result.extend(_flatten_text(item))
        return result
    try:
        return [json.dumps(value, ensure_ascii=False, default=str)]
    except TypeError:
        return [str(value)]


def _join_parts(parts: list[Any]) -> str:
    return "\n".join(
        str(part).strip()
        for part in parts
        if part is not None and str(part).strip()
    )


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_SPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
