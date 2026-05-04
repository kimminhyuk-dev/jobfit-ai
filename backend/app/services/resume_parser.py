"""
이력서 파일 텍스트 추출 및 기본 파싱 유틸리티.
LLM/임베딩 없이 정규식과 파일 포맷 파서만 사용한다.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path


class ResumeParseError(Exception):
    """이력서 텍스트 추출 실패"""


SKILL_KEYWORDS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Next.js",
    "Vue",
    "Node.js",
    "FastAPI",
    "Django",
    "Spring",
    "SQL",
    "PostgreSQL",
    "MySQL",
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
]


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
    lower_text = normalized.lower()
    compact_lower_text = compact_skill_text.lower()
    skills = [
        skill
        for skill in SKILL_KEYWORDS
        if skill.lower() in lower_text or _compact_skill_text(skill).lower() in compact_lower_text
    ]
    return {
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "skills": skills,
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
    urls = set(re.findall(r"https?://[^\s)]+", text))
    url_pattern = re.compile(r"https?\s*:\s*/\s*/\s*[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-\s]+")
    for line in text.splitlines():
        if not re.search(r"https?\s*:", line) or re.search(r"https?://[^\s)]+", line):
            continue
        for match in url_pattern.findall(line):
            compact_url = re.sub(r"\s+", "", match).rstrip(".,;")
            if re.fullmatch(r"https?://[^\s)]+", compact_url):
                urls.add(compact_url)
    return sorted(urls)


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
