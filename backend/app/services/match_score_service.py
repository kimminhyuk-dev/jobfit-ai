"""Resume-to-job matching score service."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_match_score import ApplicationMatchScore
from app.models.job_posting import JobPosting
from app.models.resume import Resume
from app.models.resume_cover_letter_section import ResumeCoverLetterSection
from app.models.resume_project import ResumeProject
from app.repositories.application_match_score_repository import (
    ApplicationMatchScoreRepository,
)
from app.repositories.resume_repository import ResumeRepository
from app.services.match_score_constants import (
    COMPACT_PATTERN,
    EMPTY_RATIO,
    EVIDENCE_RATIO_PRECISION,
    GRADE_A_MIN,
    GRADE_B_MIN,
    GRADE_C_MIN,
    INPUT_SIGNATURE_ENCODING,
    MATCH_SCORE_ALGORITHM_VERSION,
    MATCH_SCORE_BASE,
    MATCH_SCORE_MAX,
    MATCH_SCORE_MIN,
    MATCH_SCORE_MODEL,
    MATCH_SCORE_PROFILE_MAX,
    MATCH_SCORE_SKILL_KEYWORDS,
    MATCH_SCORE_SKILL_WEIGHT,
    MATCH_SCORE_TEXT_MAX,
    MATCH_SCORE_TEXT_SCALE,
    MAX_TEXT_CHARS,
    PROFILE_COVER_LETTER_POINTS,
    PROFILE_JOB_TEXT_POINTS,
    PROFILE_JOB_TITLE_POINTS,
    PROFILE_PROJECT_POINTS,
    PROFILE_RESUME_SKILL_POINTS,
    PROFILE_RESUME_TEXT_POINTS,
    REASONS_LIMIT,
    RESPONSE_SKILL_LIMIT,
    SENSITIVE_MATCH_TOKENS,
    SKILL_PREVIEW_LIMIT,
    STRENGTH_TEXT_COMPONENT_MIN,
    TOKEN_PATTERN,
)

_TOKEN_RE = re.compile(TOKEN_PATTERN)
_COMPACT_RE = re.compile(COMPACT_PATTERN)


@dataclass(frozen=True)
class _MatchResult:
    score: int
    grade: str
    summary: str
    strengths: list[str]
    gaps: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    evidence: dict[str, Any]


class MatchScoreService:
    """Calculate and persist deterministic matching scores."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ApplicationMatchScoreRepository(db)
        self.resume_repository = ResumeRepository(db)

    def ensure_score_for_application(
        self,
        application: Application,
        resume: Resume,
        job: JobPosting,
        *,
        actor_id: int | None,
        request_ip: str | None,
    ) -> ApplicationMatchScore:
        projects = self.resume_repository.get_projects(resume.resume_id)
        cover_letter_sections = self.resume_repository.get_cover_letter_sections(
            resume.resume_id
        )
        signature = _input_signature(
            resume=resume,
            job=job,
            projects=projects,
            cover_letter_sections=cover_letter_sections,
        )
        existing = self.repository.get_by_application_id(application.application_id)
        if (
            existing is not None
            and existing.input_signature == signature
            and existing.model == MATCH_SCORE_MODEL
            and existing.algorithm_version == MATCH_SCORE_ALGORITHM_VERSION
        ):
            return existing

        result = _calculate_match_score(
            resume=resume,
            job=job,
            projects=projects,
            cover_letter_sections=cover_letter_sections,
        )
        return self.repository.upsert(
            application_id=application.application_id,
            score=result.score,
            grade=result.grade,
            summary=result.summary,
            strengths=result.strengths,
            gaps=result.gaps,
            matched_skills=result.matched_skills,
            missing_skills=result.missing_skills,
            evidence=result.evidence,
            model=MATCH_SCORE_MODEL,
            algorithm_version=MATCH_SCORE_ALGORITHM_VERSION,
            input_signature=signature,
            actor_id=actor_id,
            request_ip=request_ip,
        )


def _calculate_match_score(
    *,
    resume: Resume,
    job: JobPosting,
    projects: list[ResumeProject],
    cover_letter_sections: list[ResumeCoverLetterSection],
) -> _MatchResult:
    resume_text = _resume_text(resume, projects, cover_letter_sections)
    job_text = _job_text(job)
    resume_skills = _resume_skills(resume, projects, resume_text)
    job_skills = _job_skills(job, job_text)

    resume_skill_map = _skill_map(resume_skills)
    job_skill_map = _skill_map(job_skills)
    job_skill_order = list(job_skill_map)

    matched_keys = [key for key in job_skill_order if key in resume_skill_map]
    missing_keys = [key for key in job_skill_order if key not in resume_skill_map]
    matched_skills = [job_skill_map[key] for key in matched_keys]
    missing_skills = [job_skill_map[key] for key in missing_keys]

    if job_skill_map:
        skill_ratio = len(matched_keys) / len(job_skill_map)
        skill_component = round(MATCH_SCORE_SKILL_WEIGHT * skill_ratio)
    else:
        skill_ratio = EMPTY_RATIO
        skill_component = MATCH_SCORE_MIN

    text_similarity = _token_similarity(resume_text, job_text)
    text_component = round(
        min(MATCH_SCORE_TEXT_MAX, text_similarity * MATCH_SCORE_TEXT_SCALE)
    )

    profile_component = MATCH_SCORE_MIN
    if resume.raw_text:
        profile_component += PROFILE_RESUME_TEXT_POINTS
    if resume_skill_map:
        profile_component += PROFILE_RESUME_SKILL_POINTS
    if projects:
        profile_component += PROFILE_PROJECT_POINTS
    if cover_letter_sections or (resume.parsed_data or {}).get("cover_letter"):
        profile_component += PROFILE_COVER_LETTER_POINTS
    if job.raw_content:
        profile_component += PROFILE_JOB_TEXT_POINTS
    if job.title:
        profile_component += PROFILE_JOB_TITLE_POINTS
    profile_component = min(profile_component, MATCH_SCORE_PROFILE_MAX)

    score = max(
        MATCH_SCORE_MIN,
        min(
            MATCH_SCORE_MAX,
            MATCH_SCORE_BASE
            + skill_component
            + text_component
            + profile_component,
        ),
    )
    grade = _grade(score)
    strengths = _strengths(matched_skills, projects, text_component)
    gaps = _gaps(missing_skills, bool(job_skill_map), bool(resume_skill_map))
    summary = _summary(
        score=score,
        grade=grade,
        job_skill_count=len(job_skill_map),
        matched_skill_count=len(matched_skills),
        has_job_skills=bool(job_skill_map),
    )
    evidence = {
        "components": {
            "base": MATCH_SCORE_BASE,
            "skill": skill_component,
            "text": text_component,
            "profile": profile_component,
        },
        "skill_ratio": round(skill_ratio, EVIDENCE_RATIO_PRECISION),
        "text_similarity": round(text_similarity, EVIDENCE_RATIO_PRECISION),
        "resume_skill_count": len(resume_skill_map),
        "job_skill_count": len(job_skill_map),
        "project_count": len(projects),
        "cover_letter_section_count": len(cover_letter_sections),
    }
    return _MatchResult(
        score=score,
        grade=grade,
        summary=summary,
        strengths=strengths,
        gaps=gaps,
        matched_skills=matched_skills[:RESPONSE_SKILL_LIMIT],
        missing_skills=missing_skills[:RESPONSE_SKILL_LIMIT],
        evidence=evidence,
    )


def _resume_text(
    resume: Resume,
    projects: list[ResumeProject],
    cover_letter_sections: list[ResumeCoverLetterSection],
) -> str:
    parsed = resume.parsed_data or {}
    parts: list[str] = [
        resume.title,
        resume.raw_text or "",
        *_flatten_text(parsed.get("skills")),
        *_flatten_text(parsed.get("experiences")),
        *_flatten_text(parsed.get("projects")),
        *_flatten_text(parsed.get("cover_letter")),
        *_flatten_text(parsed.get("cover_letter_sections")),
    ]
    for project in projects:
        parts.extend(
            [
                project.name or "",
                project.role or "",
                project.description or "",
                project.review or "",
                project.raw_text or "",
                *_flatten_text(project.tech_stack),
            ]
        )
    for section in cover_letter_sections:
        parts.extend([section.title, section.content])
    return _join_text(parts)


def _job_text(job: JobPosting) -> str:
    parts = [
        job.title,
        job.company_name or "",
        job.industry or "",
        job.career_level or "",
        job.education or "",
        job.employment_type or "",
        job.ncs_category or "",
        job.raw_content or "",
        *_flatten_text(job.parsed_skills),
    ]
    return _join_text(parts)


def _resume_skills(
    resume: Resume,
    projects: list[ResumeProject],
    resume_text: str,
) -> list[str]:
    parsed = resume.parsed_data or {}
    skills = _flatten_text(parsed.get("skills"))
    for project in projects:
        skills.extend(_flatten_text(project.tech_stack))
    skills.extend(_known_skills_in_text(resume_text))
    return _dedupe_text(skills)


def _job_skills(job: JobPosting, job_text: str) -> list[str]:
    skills = _flatten_text(job.parsed_skills)
    skills.extend(_known_skills_in_text(job_text))
    return _dedupe_text(skills)


def _known_skills_in_text(text: str) -> list[str]:
    lower_text = text.lower()
    compact_text = _compact_skill(text)
    found: list[str] = []
    for skill in MATCH_SCORE_SKILL_KEYWORDS:
        lower_skill = skill.lower()
        compact_skill = _compact_skill(skill)
        if lower_skill in lower_text or (compact_skill and compact_skill in compact_text):
            found.append(skill)
    return found


def _skill_map(skills: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for skill in skills:
        key = _compact_skill(skill)
        if key and key not in result:
            result[key] = skill.strip()
    return result


def _flatten_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
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
    text = str(value).strip()
    return [text] if text else []


def _join_text(parts: list[str]) -> str:
    text = "\n".join(part.strip() for part in parts if part and part.strip())
    return text[:MAX_TEXT_CHARS]


def _dedupe_text(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        key = _compact_skill(text)
        if text and key and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _compact_skill(value: str) -> str:
    return _COMPACT_RE.sub("", value.lower())


def _token_similarity(left: str, right: str) -> float:
    left_tokens = _similarity_tokens(left)
    right_tokens = _similarity_tokens(right)
    if not left_tokens or not right_tokens:
        return EMPTY_RATIO
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _similarity_tokens(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in SENSITIVE_MATCH_TOKENS
    }


def _grade(score: int) -> str:
    if score >= GRADE_A_MIN:
        return "A"
    if score >= GRADE_B_MIN:
        return "B"
    if score >= GRADE_C_MIN:
        return "C"
    return "D"


def _strengths(
    matched_skills: list[str],
    projects: list[ResumeProject],
    text_component: int,
) -> list[str]:
    strengths: list[str] = []
    if matched_skills:
        strengths.append(
            f"공고 키워드와 이력서 기술이 {len(matched_skills)}개 일치합니다: "
            f"{', '.join(matched_skills[:SKILL_PREVIEW_LIMIT])}"
        )
    if projects:
        strengths.append(f"구조화된 프로젝트 경험 {len(projects)}건을 반영했습니다.")
    if text_component >= STRENGTH_TEXT_COMPONENT_MIN:
        strengths.append("공고 본문과 이력서 서술의 핵심 단어가 일부 겹칩니다.")
    if not strengths:
        strengths.append("지원서와 공고의 기본 텍스트 정보를 바탕으로 점수를 산출했습니다.")
    return strengths[:REASONS_LIMIT]


def _gaps(
    missing_skills: list[str],
    has_job_skills: bool,
    has_resume_skills: bool,
) -> list[str]:
    gaps: list[str] = []
    if missing_skills:
        gaps.append(
            "공고 키워드 중 이력서에서 바로 확인되지 않은 항목: "
            f"{', '.join(missing_skills[:SKILL_PREVIEW_LIMIT])}"
        )
    if not has_job_skills:
        gaps.append("공고에 구조화된 스킬 키워드가 부족해 본문 유사도 비중을 높였습니다.")
    if not has_resume_skills:
        gaps.append("이력서의 구조화된 기술 키워드가 부족합니다.")
    return gaps[:REASONS_LIMIT]


def _summary(
    *,
    score: int,
    grade: str,
    job_skill_count: int,
    matched_skill_count: int,
    has_job_skills: bool,
) -> str:
    if has_job_skills:
        return (
            f"공고 키워드 {job_skill_count}개 중 {matched_skill_count}개가 "
            f"이력서에서 확인되어 {score}점({grade}등급)으로 산출했습니다."
        )
    return (
        f"구조화된 공고 스킬이 없어 본문 유사도와 이력서 완성도를 중심으로 "
        f"{score}점({grade}등급)을 산출했습니다."
    )


def _input_signature(
    *,
    resume: Resume,
    job: JobPosting,
    projects: list[ResumeProject],
    cover_letter_sections: list[ResumeCoverLetterSection],
) -> str:
    payload = {
        "resume": {
            "title": resume.title,
            "raw_text": resume.raw_text,
            "parsed_data": resume.parsed_data,
            "projects": [
                {
                    "name": p.name,
                    "role": p.role,
                    "description": p.description,
                    "review": p.review,
                    "tech_stack": p.tech_stack,
                    "raw_text": p.raw_text,
                }
                for p in projects
            ],
            "cover_letter_sections": [
                {"title": s.title, "content": s.content}
                for s in cover_letter_sections
            ],
        },
        "job": {
            "title": job.title,
            "career_level": job.career_level,
            "education": job.education,
            "employment_type": job.employment_type,
            "ncs_category": job.ncs_category,
            "raw_content": job.raw_content,
            "parsed_skills": job.parsed_skills,
        },
        "algorithm_version": MATCH_SCORE_ALGORITHM_VERSION,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode(INPUT_SIGNATURE_ENCODING)).hexdigest()
