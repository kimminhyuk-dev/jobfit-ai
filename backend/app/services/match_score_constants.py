"""Constants for deterministic application match scoring."""

from __future__ import annotations

from typing import Final

from app.services.resume_parser import SKILL_KEYWORDS as RESUME_PARSER_SKILL_KEYWORDS

MATCH_SCORE_MODEL: Final = "local-match-v1"
MATCH_SCORE_ALGORITHM_VERSION: Final = "1.0.0"

MATCH_SCORE_MIN: Final = 0
MATCH_SCORE_MAX: Final = 100
MATCH_SCORE_BASE: Final = 20
MATCH_SCORE_SKILL_WEIGHT: Final = 55
MATCH_SCORE_TEXT_MAX: Final = 25
MATCH_SCORE_TEXT_SCALE: Final = 120
MATCH_SCORE_PROFILE_MAX: Final = 20

PROFILE_RESUME_TEXT_POINTS: Final = 5
PROFILE_RESUME_SKILL_POINTS: Final = 5
PROFILE_PROJECT_POINTS: Final = 5
PROFILE_COVER_LETTER_POINTS: Final = 3
PROFILE_JOB_TEXT_POINTS: Final = 5
PROFILE_JOB_TITLE_POINTS: Final = 2

GRADE_A_MIN: Final = 85
GRADE_B_MIN: Final = 70
GRADE_C_MIN: Final = 55

MAX_TEXT_CHARS: Final = 12000
STRENGTH_TEXT_COMPONENT_MIN: Final = 10
RESPONSE_SKILL_LIMIT: Final = 12
SKILL_PREVIEW_LIMIT: Final = 5
REASONS_LIMIT: Final = 4
EVIDENCE_RATIO_PRECISION: Final = 4
EMPTY_RATIO: Final = 0.0
INPUT_SIGNATURE_ENCODING: Final = "utf-8"

TOKEN_PATTERN: Final = r"[a-z][a-z0-9+#.]{1,}|[\uac00-\ud7a3]{2,}"
COMPACT_PATTERN: Final = r"[^0-9a-z\uac00-\ud7a3+#]+"

MATCH_SCORE_SKILL_KEYWORDS: Final[tuple[str, ...]] = tuple(
    RESUME_PARSER_SKILL_KEYWORDS
)

SENSITIVE_MATCH_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "age",
        "birth",
        "birthdate",
        "birthday",
        "disability",
        "female",
        "gender",
        "male",
        "married",
        "pregnancy",
        "religion",
        "unmarried",
        "결혼",
        "국적",
        "군필",
        "기혼",
        "나이",
        "남성",
        "남자",
        "미혼",
        "민족",
        "병역",
        "생년월일",
        "성별",
        "여성",
        "여자",
        "연령",
        "임신",
        "장애",
        "종교",
        "출산",
        "출생",
    }
)
