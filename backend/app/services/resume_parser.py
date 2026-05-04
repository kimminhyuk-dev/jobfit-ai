"""
이력서 파일 텍스트 추출 및 기본 파싱 유틸리티.
LLM/임베딩 없이 정규식과 파일 포맷 파서만 사용한다.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any


class ResumeParseError(Exception):
    """이력서 텍스트 추출 실패"""


SKILL_KEYWORDS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "HTML",
    "CSS",
    "React",
    "Next.js",
    "Vue",
    "Node.js",
    "FastAPI",
    "Django",
    "Spring",
    "Spring Boot",
    "JSP",
    "jQuery",
    "REST API",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "Oracle",
    "Docker",
    "Kubernetes",
    "AWS",
    "GCP",
    "Azure",
    "Git",
    "Linux",
    "TensorFlow",
    "PyTorch",
    "LLM",
    "GitHub",
    "웹 개발",
    "백엔드",
    "프론트엔드",
]

SECTION_ALIASES = {
    "profile": [
        "인적사항",
        "기본정보",
        "개인정보",
        "지원자정보",
        "profile",
        "personal information",
    ],
    "education": ["학력", "학력사항", "education", "academic"],
    "training": ["교육", "교육사항", "교육이수", "훈련", "연수", "training"],
    "experience": [
        "경력",
        "경력사항",
        "경험",
        "업무경험",
        "실무경험",
        "work experience",
        "experience",
        "employment",
    ],
    "projects": ["프로젝트", "주요프로젝트", "수행프로젝트", "project", "projects"],
    "certifications": [
        "자격증",
        "자격사항",
        "자격 및 면허",
        "면허",
        "certification",
        "certifications",
        "certificate",
        "license",
    ],
    "skills": ["기술", "기술스택", "보유기술", "역량", "skill", "skills", "tech stack"],
    "cover_letter": [
        "자기소개서",
        "자기소개",
        "지원동기",
        "성장과정",
        "성격의 장단점",
        "입사 후 포부",
        "cover letter",
        "introduction",
        "personal statement",
    ],
    "awards": ["수상", "수상내역", "awards"],
    "languages": ["어학", "외국어", "language", "languages"],
}


def extract_resume_text(file_path: Path, content_type: str) -> str:
    suffix = file_path.suffix.lower()
    if content_type == "text/plain" or suffix == ".txt":
        return _extract_txt(file_path)
    if content_type == "application/pdf" or suffix == ".pdf":
        return _extract_pdf(file_path)
    if (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or suffix == ".docx"
    ):
        return _extract_docx(file_path)
    raise ResumeParseError("지원하지 않는 파일 형식입니다.")


def parse_resume_text(text: str) -> dict:
    normalized = re.sub(r"\s+", " ", text).strip()
    compact_contact_text = _compact_contact_text(text)
    compact_skill_text = _compact_skill_text(text)

    emails = _extract_emails(text)
    phone_candidates = re.findall(
        r"(?:\+82[-.\s]?)?0?1[016789][-\s.]?\d{3,4}[-\s.]?\d{4}",
        text,
    ) + re.findall(
        r"(?:\+82[-.]?)?0?1[016789][-.]?\d{3,4}[-.]?\d{4}",
        compact_contact_text,
    )
    phones = sorted({_normalize_phone(phone) for phone in phone_candidates})
    urls = _extract_urls(text)
    skill_search_text = _strip_urls_for_skill_search(normalized, urls)
    lower_text = skill_search_text.lower()
    compact_lower_text = _compact_skill_text(skill_search_text).lower()
    skills = [
        skill
        for skill in SKILL_KEYWORDS
        if _has_skill(lower_text, compact_lower_text, skill)
    ]
    sections = _detect_sections(text)
    profile = _extract_profile(text, emails, phones, urls)
    highlights = _extract_resume_highlights(text, sections)
    return {
        "profile": profile,
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "skills": skills,
        "sections": sections,
        "education": _section_lines(sections, "education"),
        "training": _section_lines(sections, "training"),
        "experiences": _section_lines(sections, "experience"),
        "projects": _section_lines(sections, "projects"),
        "certifications": _section_lines(sections, "certifications"),
        "cover_letter": sections.get("cover_letter"),
        "awards": _section_lines(sections, "awards"),
        "languages": _section_lines(sections, "languages"),
        "highlights": highlights,
        "text_length": len(normalized),
    }


def _extract_txt(file_path: Path) -> str:
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ResumeParseError("텍스트 파일 인코딩을 확인할 수 없습니다.")


def _compact_contact_text(text: str) -> str:
    """PDF 추출 시 연락처/URL 문자가 벌어진 케이스를 정규식용으로 보정한다."""
    return re.sub(r"(?<=[A-Za-z0-9@._+\-:/])\s+(?=[A-Za-z0-9@._+\-:/])", "", text)


def _compact_skill_text(text: str) -> str:
    """PDF 추출 시 J A V A처럼 벌어진 영문 기술명을 검색할 수 있게 보정한다."""
    return re.sub(r"[^A-Za-z0-9+#.]+", "", text)


def _has_skill(lower_text: str, compact_lower_text: str, skill: str) -> bool:
    lower_skill = skill.lower()
    if _contains_skill_phrase(lower_text, lower_skill):
        return True
    compact_skill = _compact_skill_text(skill).lower()
    if compact_skill in {"git"}:
        return False
    return bool(compact_skill and compact_skill in compact_lower_text)


def _contains_skill_phrase(lower_text: str, lower_skill: str) -> bool:
    if re.search(r"[가-힣]", lower_skill):
        return lower_skill in lower_text
    escaped = re.escape(lower_skill)
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", lower_text))


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("82"):
        digits = "0" + digits[2:]
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return phone


def _extract_emails(text: str) -> list[str]:
    emails = set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text))
    email_pattern = re.compile(
        r"(?:[A-Za-z0-9._%+\-]\s*)+@\s*(?:[A-Za-z0-9\-]\s*)+"
        r"(?:\.\s*(?:[A-Za-z]\s*){2,})+"
    )
    for line in text.splitlines():
        if "@" not in line or re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", line):
            continue
        for match in email_pattern.findall(line):
            compact_email = re.sub(r"\s+", "", match)
            if re.fullmatch(r"[\w.+-]+@[\w-]+(?:\.[A-Za-z]{2,})+", compact_email):
                emails.add(compact_email)
    return sorted(emails)


def _extract_urls(text: str) -> list[str]:
    urls = set(_clean_url(url) for url in re.findall(r"https?://[^\s)]+", text))
    bare_url_pattern = re.compile(
        r"(?<![@A-Za-z0-9._%+\-])"
        r"(?:github\.com|gitlab\.com|linkedin\.com|velog\.io|notion\.site|"
        r"blog\.naver\.com|[A-Za-z0-9-]+\.(?:com|net|org|io|dev|kr))"
        r"/?[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-]*",
        re.IGNORECASE,
    )
    url_pattern = re.compile(
        r"(?:h\s*t\s*t\s*p\s*s?|https?)\s*:\s*/\s*/\s*"
        r"[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-\s]+",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        for match in bare_url_pattern.findall(_compact_contact_text(line)):
            urls.add(_clean_url(match))
        if not re.search(r"(?:h\s*t\s*t\s*p\s*s?|https?)\s*:", line, re.IGNORECASE):
            continue
        for match in url_pattern.findall(line):
            compact_url = re.sub(r"\s+", "", match)
            compact_url = re.sub(r"^h\s*t\s*t\s*p", "http", compact_url, flags=re.IGNORECASE)
            compact_url = _clean_url(compact_url)
            if re.fullmatch(r"https?://[^\s)]+", compact_url):
                urls.add(compact_url)
    return sorted(url for url in urls if url)


def _clean_url(url: str) -> str:
    cleaned = url.strip().rstrip(".,;)]}")
    if cleaned and not re.match(r"https?://", cleaned, re.IGNORECASE):
        cleaned = f"https://{cleaned}"
    return cleaned


def _strip_urls_for_skill_search(text: str, urls: list[str]) -> str:
    stripped = text
    for url in urls:
        stripped = stripped.replace(url, " ")
        stripped = stripped.replace(re.sub(r"^https?://", "", url), " ")
    return stripped


def _extract_profile(
    text: str,
    emails: list[str],
    phones: list[str],
    urls: list[str],
) -> dict[str, Any]:
    lines = _normalized_lines(text)
    return {
        "name": _extract_name(lines),
        "birth_date": _extract_birth_date(text),
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
        "urls": urls,
        "address": _extract_labeled_value(lines, ["주소", "거주지"]),
    }


def _extract_name(lines: list[str]) -> str | None:
    labeled = _extract_labeled_value(lines, ["이름", "성명", "지원자"])
    if labeled:
        return labeled
    for line in lines[:15]:
        compact = re.sub(r"\s+", "", line)
        if re.fullmatch(r"[가-힣]{2,5}", compact) and compact not in SECTION_ALIASES:
            return compact
    return None


def _extract_birth_date(text: str) -> str | None:
    match = re.search(
        r"(?:생년월일|출생|나이)?\s*((?:19|20)\d{2})[.\-/년\s]+(\d{1,2})[.\-/월\s]+(\d{1,2})",
        text,
    )
    if not match:
        return None
    year, month, day = match.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def _extract_labeled_value(lines: list[str], labels: list[str]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    for line in lines:
        match = re.search(rf"(?:{label_pattern})\s*[:：]?\s*(.+)", line, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


def _detect_sections(text: str) -> dict[str, str]:
    lines = _normalized_lines(text)
    sections: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in lines:
        section_key = _classify_section_header(line)
        if section_key:
            current_key = section_key
            sections.setdefault(current_key, [])
            continue
        if current_key:
            sections[current_key].append(line)

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
        if "\n".join(value).strip()
    }


def _classify_section_header(line: str) -> str | None:
    compact_line = _compact_header_text(line)
    if len(compact_line) > 40:
        return None
    for key, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            compact_alias = _compact_header_text(alias)
            if compact_line == compact_alias or compact_line.startswith(compact_alias):
                return key
    return None


def _compact_header_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", text).lower()


def _normalized_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _section_lines(sections: dict[str, str], key: str) -> list[str]:
    section = sections.get(key)
    if not section:
        return []
    return [line for line in section.splitlines() if line.strip()]


def _extract_resume_highlights(text: str, sections: dict[str, str]) -> dict[str, list[str]]:
    return {
        "career_lines": _find_lines(text, ["경력", "개발자", "엔지니어", "근무", "담당"]),
        "education_lines": _section_lines(sections, "education")
        or _find_lines(text, ["대학교", "대학", "고등학교", "학과", "졸업", "재학"]),
        "certification_lines": _section_lines(sections, "certifications")
        or _find_lines(text, ["기사", "산업기사", "자격증", "certificate", "certification"]),
        "cover_letter_lines": _section_lines(sections, "cover_letter"),
    }


def _find_lines(text: str, keywords: list[str], limit: int = 12) -> list[str]:
    lines = _normalized_lines(text)
    matches = [
        line
        for line in lines
        if any(keyword.lower() in line.lower() for keyword in keywords)
    ]
    return matches[:limit]


def _extract_pdf(file_path: Path) -> str:
    try:
        pypdf = importlib.import_module("pypdf")
    except ImportError as exc:
        raise ResumeParseError("PDF 파싱 라이브러리(pypdf)가 설치되어 있지 않습니다.") from exc

    try:
        reader = pypdf.PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 - 외부 파일 파서 오류를 도메인 오류로 감싼다.
        raise ResumeParseError("PDF 텍스트 추출에 실패했습니다.") from exc
    return "\n".join(pages).strip()


def _extract_docx(file_path: Path) -> str:
    try:
        docx = importlib.import_module("docx")
    except ImportError as exc:
        raise ResumeParseError(
            "DOCX 파싱 라이브러리(python-docx)가 설치되어 있지 않습니다."
        ) from exc

    try:
        document = docx.Document(str(file_path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
    except Exception as exc:  # noqa: BLE001
        raise ResumeParseError("DOCX 텍스트 추출에 실패했습니다.") from exc
    return "\n".join(paragraphs).strip()
