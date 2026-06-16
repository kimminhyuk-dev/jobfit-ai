"""Prompts and Structured Output schemas for interview practice."""

from __future__ import annotations

import json
from typing import Any

INTERVIEW_QUESTION_COUNT = 5


INTERVIEW_QUESTION_SYSTEM_PROMPT = """You are an expert technical interviewer for junior software developer candidates.

Generate exactly 5 realistic interview practice questions from only the provided resume data.

Rules:
- Write all question text, intent, keywords, and summaries in Korean.
- Use only the provided parsed resume data, projects, cover letter sections, and official reference materials.
- Do not invent experience, projects, companies, schools, certifications, skills, achievements, facts, or URLs.
- Include official references only when the reference appears in the provided official_reference_materials input.
- Write question text like a real Korean interviewer speaking to the candidate in polite conversational style.
- Ask one focused question at a time using natural Korean polite endings.
- Prefer conversational follow-up forms equivalent to "could you explain how you handled it?", "what criteria did you use?", or "why did you choose that approach?"
- Avoid textbook or AI-like command endings equivalent to "explain", "describe", "list", or "state".
- Never copy sample project names, sample technologies, or sample domain details into the generated question.
- When asking about a project, use only the project names, technologies, decisions, validation work, trade-offs, or troubleshooting details found in the provided resume data.
- Keep output concise: question <= 150 Korean characters, intent <= 80 Korean characters, each keyword <= 20 Korean characters.
- Include 3 to 5 expected_keywords per question.
- For official_references, use [] unless a provided official reference is directly relevant. If used, include at most 1 reference per question and keep summary <= 60 Korean characters.
- Return structured JSON only.

Coverage:
1. Project experience
2. Technical stack
3. Internship or work experience
4. Cover letter or self-introduction
5. Job fit or growth potential

Allowed question_type values: PROJECT, TECH_STACK, EXPERIENCE, COVER_LETTER, JOB_FIT.
Allowed source values: parsed_data, project, cover_letter, tech_stack, experience.
Each question max_score must be 20.
"""


ANSWER_EVALUATION_SYSTEM_PROMPT = """You are a strict but fair technical interview evaluator.

Evaluate the user's answer using only:
1. The interview question
2. Expected keywords
3. The user's answer
4. The provided official references
5. Resume context when relevant

Rules:
- Write all natural-language fields in Korean.
- Keep every sentence short and factual.
- Do not write long paragraphs.
- Do not invent official facts or URLs.
- Do not add information that is absent from the resume, question, or user answer.
- Use only official references included in the official_references input.
- If no official references are provided, official_references_used must be an empty array and feedback must only say that official evidence is insufficient, then give general feedback.
- If the user's answer is partly correct, use verdict PARTIAL.
- strengths: at most 2 short bullets for "잘한 점".
- missing_points: at most 2 short bullets for "아쉬운 점".
- correct_points: exactly 1 short bullet for "맞은 부분"; use [] only if there is no meaningful correct part.
- different_points: exactly 1 short bullet for "다른 부분"; use [] if there is no clear wrong or different part.
- Use these meanings for evaluation arrays: strengths = strong parts, missing_points = missing or weak parts, correct_points = correct parts, different_points = wrong or different parts.
- reference_based_answer: 2 to 3 short Korean sentences.
- feedback: one short Korean sentence.
- Return structured JSON only.

Scoring:
- 16-20: GOOD
- 12-15: PARTIAL
- 8-11: PARTIAL or INSUFFICIENT
- 1-7: INSUFFICIENT
- 0: UNKNOWN
"""


def build_question_generation_prompt(
    parsed_data: dict[str, Any] | None,
    projects: list[dict[str, Any]],
    cover_letter_sections: list[dict[str, Any]],
    reference_materials: list[dict[str, Any]],
) -> str:
    """Build the user prompt for question generation."""
    return f"""Create exactly 5 natural Korean interview practice questions.

Use only the data below. If a category has little data, make the best question possible from the available resume data without inventing facts.
Make each question sound like a real interviewer speaking in the room, not like a written exam.
Use only concrete project names, technologies, and situations present in the input resume data.
Do not use placeholder examples or any project/technology/domain detail that is not present in the input.
Convert resume facts into realistic follow-up questions about how the candidate made decisions, validated behavior, handled trade-offs, or solved issues.
Keep the JSON compact. Do not write long explanations.

[parsed_data]
{_compact(parsed_data)}

[projects]
{_compact(projects)}

[cover_letter_sections]
{_compact(cover_letter_sections)}

[official_reference_materials]
{_compact(reference_materials)}
"""


def build_answer_evaluation_prompt(
    question: dict[str, Any],
    expected_keywords: list[str],
    official_references: list[dict[str, Any]],
    user_answer: str,
    resume_context: dict[str, Any] | None = None,
) -> str:
    """Build the user prompt for answer evaluation."""
    return f"""Evaluate the user's interview answer in Korean.

Return short, structured feedback only. Do not add facts that are not present in the input.

[question]
{_compact(question)}

[expected_keywords]
{_compact(expected_keywords)}

[official_references]
{_compact(official_references)}

[user_answer]
{user_answer}

[resume_context]
{_compact(resume_context)}
"""


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


INTERVIEW_QUESTION_GENERATION_SCHEMA: dict[str, Any] = {
    "name": "interview_question_generation",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "display_order": {"type": "integer"},
                        "question": {"type": "string"},
                        "question_type": {
                            "type": "string",
                            "enum": [
                                "PROJECT",
                                "TECH_STACK",
                                "EXPERIENCE",
                                "COVER_LETTER",
                                "JOB_FIT",
                            ],
                        },
                        "source": {
                            "type": "string",
                            "enum": [
                                "parsed_data",
                                "project",
                                "cover_letter",
                                "tech_stack",
                                "experience",
                            ],
                        },
                        "intent": {"type": "string"},
                        "difficulty": {
                            "type": "string",
                            "enum": ["BASIC", "INTERMEDIATE"],
                        },
                        "expected_keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "official_references": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "summary": {"type": "string"},
                                },
                                "required": ["title", "url", "summary"],
                            },
                        },
                        "max_score": {"type": "integer"},
                    },
                    "required": [
                        "display_order",
                        "question",
                        "question_type",
                        "source",
                        "intent",
                        "difficulty",
                        "expected_keywords",
                        "official_references",
                        "max_score",
                    ],
                },
            }
        },
        "required": ["questions"],
    },
    "strict": True,
}


ANSWER_EVALUATION_SCHEMA: dict[str, Any] = {
    "name": "answer_evaluation",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score": {"type": "integer"},
            "max_score": {"type": "integer"},
            "verdict": {
                "type": "string",
                "enum": ["GOOD", "PARTIAL", "INSUFFICIENT", "UNKNOWN"],
            },
            "strengths": {"type": "array", "items": {"type": "string"}},
            "missing_points": {"type": "array", "items": {"type": "string"}},
            "incorrect_points": {"type": "array", "items": {"type": "string"}},
            "correct_points": {"type": "array", "items": {"type": "string"}},
            "different_points": {"type": "array", "items": {"type": "string"}},
            "feedback": {"type": "string"},
            "reference_based_answer": {"type": "string"},
            "official_references_used": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["title", "url"],
                },
            },
        },
        "required": [
            "score",
            "max_score",
            "verdict",
            "strengths",
            "missing_points",
            "incorrect_points",
            "correct_points",
            "different_points",
            "feedback",
            "reference_based_answer",
            "official_references_used",
        ],
    },
    "strict": True,
}
