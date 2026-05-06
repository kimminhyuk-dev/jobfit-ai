"""
이력서 파일 텍스트 추출 및 파싱 유틸리티.
GEMINI_API_KEY가 없으면 정규식 기반 파싱으로 폴백한다.
"""

from __future__ import annotations

import importlib
import json as _json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
        "학창시절",
        "자신의 장단점",
        "성격의 장단점",
        "입사 후 포부",
        "cover letter",
        "introduction",
        "personal statement",
    ],
    "awards": ["수상", "수상내역", "awards"],
    "languages": ["어학", "외국어", "language", "languages"],
}

# 자기소개서 소제목: 섹션 전환 후에도 텍스트에 포함되어야 할 항목
COVER_LETTER_SECTION_LABELS = [
    "지원동기",
    "성장과정",
    "학창시절",
    "자신의 장단점",
    "성격의 장단점",
    "입사 후 포부",
    "포부",
]

# compact 형태로 미리 계산 (_compact_header_text 와 동일 규칙: 비알파뉴메릭 제거 + 소문자)
_COVER_LETTER_SUBSECTION_COMPACT = frozenset({
    "지원동기", "성장과정", "학창시절", "자신의장단점", "성격의장단점", "입사후포부", "포부",
})

SCHOOL_LEVEL_PATTERNS: list[tuple[str, str]] = [
    ("university", r"[가-힣A-Za-z0-9]+대학원"),
    ("university", r"[가-힣A-Za-z0-9]+대학교"),
    ("college", r"[가-힣A-Za-z0-9]+대학(?!교|원)"),
    ("high", r"[가-힣A-Za-z0-9]+고등학교"),
    ("middle", r"[가-힣A-Za-z0-9]+중학교"),
    ("elementary", r"[가-힣A-Za-z0-9]+초등학교"),
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
    skill_search_text = _strip_urls_for_skill_search(normalized, urls)
    lower_text = skill_search_text.lower()
    compact_lower_text = _compact_skill_text(skill_search_text).lower()
    skills = [
        skill
        for skill in SKILL_KEYWORDS
        if _has_skill(lower_text, compact_lower_text, skill)
    ]
    sections = _detect_sections(text)
    schools = _extract_schools(text, sections)
    profile = _extract_profile(text, emails, phones, urls)
    highlights = _extract_resume_highlights(text, sections)
    cover_letter_text = sections.get("cover_letter")
    return {
        "profile": profile,
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "skills": skills,
        "sections": sections,
        "schools": schools,
        "education": _section_lines(sections, "education"),
        "training": _section_lines(sections, "training"),
        "experiences": _section_lines(sections, "experience"),
        "projects": _group_section_items(sections.get("projects", "")),
        "certifications": _section_lines(sections, "certifications"),
        "cover_letter": cover_letter_text,
        "cover_letter_sections": _parse_cover_letter_sections(cover_letter_text),
        "awards": _section_lines(sections, "awards"),
        "languages": _section_lines(sections, "languages"),
        "highlights": highlights,
        "text_length": len(normalized),
    }


_LLM_SYSTEM_PROMPT = """당신은 한국어 이력서 파싱 전문가입니다. 이력서 텍스트를 분석해 구조화된 JSON만 반환합니다.

반환 형식 (JSON 외 다른 텍스트 절대 금지):
{
  "name": "이름 (2-5자 한글 인명) 또는 null",
  "birth_date": "YYYY-MM-DD 또는 null",
  "address": "주소 또는 null",
  "education": ["학교명·전공·학위·기간·상태를 1줄로 합쳐서 항목마다 1개"],
  "training": ["기관명·과정명·기간을 1줄로 합쳐서 항목마다 1개"],
  "experiences": ["회사명·직책·기간·업무내용을 1줄 또는 여러 줄로 항목마다 1개"],
  "projects": ["프로젝트명·기간·설명·기술스택을 1줄 또는 여러 줄로 항목마다 1개"],
  "certifications": ["자격증명·발급기관·취득일을 1줄로 항목마다 1개"],
  "skills": ["기술 키워드 단어 단위"],
  "awards": ["수상명·수여기관·날짜를 1줄로 항목마다 1개"],
  "languages": ["언어·수준·점수를 1줄로 항목마다 1개"],
  "cover_letter": "자기소개서·지원동기·성장과정·입사포부·성격장단점 전체 텍스트 또는 null"
}

처리 규칙:
1. HWP/한컴 PDF 인코딩 아티팩트 제거: 공백·줄바꿈·점 바로 뒤에 오는 단독 소문자 'r'을 모두 제거할 것
   예: 'r학과'→'학과', 'rSI/SM'→'SI/SM', 'r파견'→'파견', 'r07.16'→'07.16', 'r보내'→'보내', 'r업무'→'업무'
   단, 정상 단어 내부의 r (예: Korea, Spring, work)은 절대 제거하지 말 것

2. 이름(name) 추출 규칙:
   - '이력서', '履歷書', 'RESUME', 'CV', 'Curriculum Vitae' 등 서류 제목은 이름이 아니므로 절대 사용하지 말 것
   - 실제 2~5자 한글 인명을 찾을 것. 이름 레이블('이름:', '성명:') 뒤에 오는 값을 우선 사용할 것
   - 이름을 찾을 수 없으면 null

3. 섹션 분류 규칙:
   - 'PROGRAMMING SKILLS', 'TECH STACK', '기술스택', '보유기술' → skills에 키워드 단위로 분리
   - 자기소개, 지원동기, 성격의 장단점, 성장과정, 입사 후 포부 내용 → cover_letter
   - 학원·부트캠프·교육기관·연수 → training (education이 아님)
   - 대학교·대학원·고등학교 → education
   - 회사에서 한 업무·직책·재직기간 → experiences
   - 개발한 서비스·앱·시스템 → projects

4. 없는 섹션은 빈 배열 [], 없는 단일값은 null
5. 텍스트 전체를 빠짐없이 분석하고 내용이 잘리지 않도록 할 것"""

# Free Tier에서 사용 가능한 모델 우선순위 목록
_GEMINI_MODEL_CANDIDATES = [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]


def parse_resume_with_llm(raw_text: str, api_key: str) -> dict:
    """Gemini로 이력서 섹션을 구조화한다.
    연락처(이메일·전화·URL)는 정규식으로 별도 추출해 신뢰도를 높인다.
    모델은 Free Tier 가용 여부에 따라 순서대로 시도한다.
    """
    genai = importlib.import_module("google.generativeai")
    genai.configure(api_key=api_key)

    emails = _extract_emails(raw_text)
    compact_contact = _compact_contact_text(raw_text)
    phone_candidates = re.findall(
        r"(?:\+82[-.\s]?)?0?1[016789][-\s.]?\d{3,4}[-\s.]?\d{4}", raw_text
    ) + re.findall(r"(?:\+82[-.]?)?0?1[016789][-.]?\d{3,4}[-.]?\d{4}", compact_contact)
    phones = sorted({_normalize_phone(p) for p in phone_candidates})
    urls = _extract_urls(raw_text)

    last_exc: Exception | None = None
    response = None
    used_model: str = ""
    for model_name in _GEMINI_MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=_LLM_SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(raw_text[:8000])
            used_model = model_name
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini 모델 %s 실패: %s", model_name, exc)
            last_exc = exc

    if response is None:
        raise last_exc or RuntimeError("모든 Gemini 모델 호출 실패")

    llm = _json.loads(response.text)
    normalized = re.sub(r"\s+", " ", raw_text).strip()
    return {
        "profile": {
            "name": llm.get("name"),
            "birth_date": llm.get("birth_date"),
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "github_url": _extract_github_url(urls),
            "urls": urls,
            "address": llm.get("address"),
        },
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "skills": llm.get("skills", []),
        "sections": {},
        "schools": [],
        "education": llm.get("education", []),
        "training": llm.get("training", []),
        "experiences": llm.get("experiences", []),
        "projects": llm.get("projects", []),
        "certifications": llm.get("certifications", []),
        "cover_letter": llm.get("cover_letter"),
        "cover_letter_sections": _parse_cover_letter_sections(llm.get("cover_letter")),
        "awards": llm.get("awards", []),
        "languages": llm.get("languages", []),
        "highlights": {},
        "text_length": len(normalized),
        "parsed_by": f"llm:{used_model}",
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
            compact_url = re.sub(
                r"^h\s*t\s*t\s*p", "http", compact_url, flags=re.IGNORECASE
            )
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
        "github_url": _extract_github_url(urls),
        "urls": urls,
        "address": _extract_labeled_value(lines, ["주소", "거주지"]),
    }


def _extract_github_url(urls: list[str]) -> str | None:
    for url in urls:
        if re.search(r"github\.com/[A-Za-z0-9_.-]+", url, re.IGNORECASE):
            return url
    return None


def _extract_schools(text: str, sections: dict[str, str]) -> list[dict]:
    """학교 정보를 학교급별로 추출한다. 이력서에 명시된 학교만 반환한다."""
    search_text = sections.get("education", "") or sections.get("training", "") or text
    schools: list[dict] = []
    seen: set[str] = set()
    for line in search_text.splitlines():
        line = line.strip()
        if not line:
            continue
        for level, pattern in SCHOOL_LEVEL_PATTERNS:
            match = re.search(pattern, line)
            if match:
                name = match.group(0)
                if name not in seen:
                    seen.add(name)
                    schools.append({"type": level, "name": name, "raw": line})
                break
    return schools


_NAME_CONTAMINATING_LABELS = [
    "이메일",
    "전화번호",
    "전화",
    "연락처",
    "주소",
    "생년월일",
    "성별",
    "국적",
    "직책",
    "부서",
]


def _extract_name(lines: list[str]) -> str | None:
    labeled = _extract_labeled_value(lines, ["이름", "성명", "지원자"])
    if labeled:
        # 테이블 형식 PDF에서 이름 줄에 다른 필드 레이블이 섞이는 경우 잘라낸다
        # ("이름: 김철수 이메일: ..." → "김철수")
        for other in _NAME_CONTAMINATING_LABELS:
            idx = labeled.find(other)
            if idx != -1:
                labeled = labeled[:idx].strip()
        compact = re.sub(r"\s+", "", labeled)
        if compact and re.fullmatch(r"[가-힣]{2,5}", compact):
            return compact
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
            # 자기소개서 소제목은 섹션 헤더로 처리하면서 내용에도 포함:
            # _parse_cover_letter_sections 가 구조화 시 소제목을 구분자로 활용
            if section_key == "cover_letter" and _compact_header_text(line) in _COVER_LETTER_SUBSECTION_COMPACT:
                sections[current_key].append(line)
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
            if compact_line == compact_alias:
                return key
            if compact_line.startswith(compact_alias):
                # 앨리어스 뒤에 한글·영문이 오면 본문 제목(예: "프로젝트 1차: 쇼핑몰")이므로 헤더로 보지 않음
                remainder = compact_line[len(compact_alias):]
                if not re.search(r"[가-힣A-Za-z]", remainder):
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


def _extract_resume_highlights(
    text: str, sections: dict[str, str]
) -> dict[str, list[str]]:
    return {
        "career_lines": _find_lines(
            text, ["경력", "개발자", "엔지니어", "근무", "담당"]
        ),
        "education_lines": _section_lines(sections, "education")
        or _find_lines(text, ["대학교", "대학", "고등학교", "학과", "졸업", "재학"]),
        "certification_lines": _section_lines(sections, "certifications")
        or _find_lines(
            text, ["기사", "산업기사", "자격증", "certificate", "certification"]
        ),
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


def _group_section_items(text: str) -> list[str]:
    """빈 줄을 구분자로 섹션 텍스트를 개별 항목 블록으로 그룹화한다.

    예: 프로젝트 섹션의 각 프로젝트를 별도 항목으로 분리.
    """
    if not text:
        return []
    groups: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            groups.append("\n".join(current))
            current = []
    if current:
        groups.append("\n".join(current))
    return groups


def _parse_cover_letter_sections(text: str | None) -> dict[str, str]:
    """자기소개서 텍스트에서 소제목별로 내용을 분리한다."""
    if not text:
        return {}
    result: dict[str, list[str]] = {}
    current_title: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        matched = _match_cover_letter_subsection(stripped)
        if matched:
            current_title = matched
            result.setdefault(current_title, [])
        elif current_title:
            result[current_title].append(stripped)
    return {
        title: "\n".join(lines).strip()
        for title, lines in result.items()
        if "\n".join(lines).strip()
    }


def _match_cover_letter_subsection(line: str) -> str | None:
    compact = _compact_header_text(line)
    for label in COVER_LETTER_SECTION_LABELS:
        if compact == _compact_header_text(label):
            return label
    return None


def _normalize_pdf_text(text: str) -> str:
    """PDF 추출 텍스트에서 자주 발생하는 인코딩 깨짐을 복원한다.

    처리 순서:
    1. 전각 문자(ａ→a, Ａ→A 등) → 반각 ASCII 변환 (NFKC)
    2. HWP/한컴 PDF 폰트 인코딩 아티팩트 'r' 제거
    3. 반각/전각 카타카나(ﾅ→ナ 등)를 줄바꿈으로 치환
       — 한국 HWP/PDF 도구에서 단어 구분자로 오인코딩되는 케이스
    4. 줄 단위 공백 정리 후 'J a v a' 같은 분리 영문자 복원
    5. 텍스트 과반이 단일 음절 분리 인코딩이면 한글도 복원
    """
    # 1. 전각 → 반각
    text = unicodedata.normalize("NFKC", text)
    # 2. HWP/한컴 PDF 폰트 커스텀 인코딩 아티팩트 제거
    #    독립 소문자 'r'이 한글·괄호 앞에 오는 패턴 ('r학과', 'r(졸업)', 'r파견')
    text = re.sub(r"(?<![A-Za-z0-9])r(?=[가-힣(（「『【〔])", "", text)
    #    독립 소문자 'r'이 영문 대문자 앞에 오는 패턴 ('rSI/SM', 'rJAVA', 'rBack-End')
    text = re.sub(r"(?<![A-Za-z0-9])r(?=[A-Z])", "", text)
    #    날짜·숫자 앞 독립 'r' 제거 ('r07.16~', '2025.r10.15' 등)
    text = re.sub(r"(?<=[ \t.])r(?=\d{1,2}[.\-~/ ])", "", text)
    # 3. 카타카나를 줄바꿈으로 치환 (단어 구분자 역할을 했으므로 공백 대신 \n 사용)
    text = re.sub(r"[぀-ヿ･-ﾟ]+", "\n", text)
    # Latin fix 이전에 분리 인코딩 감지 (Latin fix 후 토큰 수가 줄어 감지 실패 방지)
    is_spaced = _is_spaced_char_encoding(text)
    # 4. 줄 단위로 영문 분리 문자 복원 후 공백 정리
    #    순서 중요: 분리 문자 복원을 먼저 해야 double-space 단어 경계가 보존됨
    cleaned: list[str] = []
    for line in text.splitlines():
        line = _fix_latin_spaced_chars(line.strip())
        line = re.sub(r"[ \t]{2,}", " ", line).strip()
        if line:
            cleaned.append(line)
    text = "\n".join(cleaned)
    # 5. 한글 음절 분리 인코딩이면 한글도 복원
    if is_spaced:
        text = "\n".join(_fix_korean_spaced_chars(ln) for ln in text.splitlines())
        text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_spaced_char_encoding(text: str) -> bool:
    """텍스트 토큰의 절반 이상이 단일 한글/영문 음절이면 분리 인코딩으로 판단한다."""
    tokens = [t for t in text.split() if re.match(r"[가-힣A-Za-z]", t)]
    if len(tokens) < 30:
        return False
    single = sum(1 for t in tokens if len(t) == 1)
    return single / len(tokens) > 0.5


def _fix_latin_spaced_chars(text: str) -> str:
    """'J a v a S c r i p t' 처럼 공백으로 분리된 3자 이상 영문자를 단어로 복원한다."""

    def collapse(m: re.Match) -> str:
        return re.sub(r"\s+", "", m.group(0))

    return re.sub(
        r"(?<![A-Za-z])([A-Za-z])(?:[ \t][A-Za-z]){2,}(?![A-Za-z])",
        collapse,
        text,
    )


def _fix_korean_spaced_chars(text: str) -> str:
    """'그 린 에 코 스' 처럼 음절 단위로 분리된 한글을 복원한다."""

    def collapse(m: re.Match) -> str:
        return re.sub(r"\s+", "", m.group(0))

    return re.sub(
        r"(?<![가-힣])([가-힣])(?:[ \t][가-힣])+(?![가-힣])",
        collapse,
        text,
    )


def _extract_pdf(file_path: Path) -> str:
    # pdfplumber: 레이아웃 기반 추출로 복잡한 PDF에서 더 정확한 결과 제공
    try:
        pdfplumber = importlib.import_module("pdfplumber")
        with pdfplumber.open(str(file_path)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return _normalize_pdf_text("\n".join(pages).strip())
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        pass

    # fallback: pypdf
    try:
        pypdf = importlib.import_module("pypdf")
    except ImportError as exc:
        raise ResumeParseError(
            "PDF 파싱 라이브러리(pypdf)가 설치되어 있지 않습니다."
        ) from exc

    try:
        reader = pypdf.PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 - 외부 파일 파서 오류를 도메인 오류로 감싼다.
        raise ResumeParseError("PDF 텍스트 추출에 실패했습니다.") from exc
    return _normalize_pdf_text("\n".join(pages).strip())


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
