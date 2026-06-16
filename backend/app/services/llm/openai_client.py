"""OpenAI client wrapper for resume interview practice."""

from __future__ import annotations

import importlib
import json
import logging
from typing import Any

from app.core.config import settings
from app.prompts.resume_interview import (
    ANSWER_EVALUATION_SCHEMA,
    ANSWER_EVALUATION_SYSTEM_PROMPT,
    INTERVIEW_QUESTION_GENERATION_SCHEMA,
    INTERVIEW_QUESTION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

QUESTION_GENERATION_MIN_OUTPUT_TOKENS = 3000


class OpenAIClientError(Exception):
    """OpenAI call or response parsing failed."""


class OpenAINotConfiguredError(OpenAIClientError):
    """OpenAI API key is missing."""


class OpenAIClient:
    """Thin wrapper around the OpenAI Responses API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        max_output_tokens: int | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model
        self.max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else settings.openai_max_output_tokens
        )
        self.reasoning_effort = (
            reasoning_effort
            if reasoning_effort is not None
            else settings.openai_reasoning_effort
        )

    @property
    def model_name(self) -> str:
        return self.model

    def generate_interview_questions(self, user_prompt: str) -> dict[str, Any]:
        """Generate exactly 5 interview practice questions."""
        return self._complete_json(
            system_prompt=INTERVIEW_QUESTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=INTERVIEW_QUESTION_GENERATION_SCHEMA,
            max_output_tokens=max(
                self.max_output_tokens,
                QUESTION_GENERATION_MIN_OUTPUT_TOKENS,
            ),
        )

    def evaluate_interview_answer(self, user_prompt: str) -> dict[str, Any]:
        """Evaluate one submitted interview answer."""
        return self._complete_json(
            system_prompt=ANSWER_EVALUATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=ANSWER_EVALUATION_SCHEMA,
        )

    def _complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: dict[str, Any],
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise OpenAINotConfiguredError("OPENAI_API_KEY is not configured.")

        try:
            openai = importlib.import_module("openai")
        except ImportError as exc:  # pragma: no cover
            raise OpenAIClientError("The openai package is not installed.") from exc

        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_output_tokens": max_output_tokens or self.max_output_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema["name"],
                    "schema": schema["schema"],
                    "strict": schema.get("strict", True),
                }
            },
        }
        # reasoning 모델(gpt-5 계열, o 시리즈)만 reasoning.effort를 받는다.
        # 낮은 effort는 추론 토큰을 줄여 응답 지연을 크게 단축한다.
        if self.reasoning_effort and _supports_reasoning(self.model):
            request_kwargs["reasoning"] = {"effort": self.reasoning_effort}

        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.responses.create(**request_kwargs)
        except Exception as exc:  # noqa: BLE001 - SDK exceptions vary by version
            logger.warning(
                "OpenAI API call failed: %s: %s",
                exc.__class__.__name__,
                _safe_error_message(exc),
            )
            raise OpenAIClientError("OpenAI API call failed.") from exc

        text = _extract_output_text(response)
        if not text:
            logger.warning("OpenAI response did not include output_text")
            raise OpenAIClientError("OpenAI response was empty.")

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("OpenAI response JSON parsing failed: %s", exc)
            raise OpenAIClientError("OpenAI response was not valid JSON.") from exc


def _supports_reasoning(model: str) -> bool:
    """reasoning.effort 파라미터를 지원하는 모델인지 판별한다."""
    name = (model or "").lower()
    return name.startswith("gpt-5") or name.startswith("o1") or name.startswith("o3") or name.startswith("o4")


def _extract_output_text(response: Any) -> str:
    """Extract text from a Responses API response object."""
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    parts: list[str] = []
    for item in getattr(response, "output", None) or []:
        for block in getattr(item, "content", None) or []:
            block_text = getattr(block, "text", None)
            if isinstance(block_text, str):
                parts.append(block_text)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
    return "\n".join(parts).strip()


def _safe_error_message(exc: Exception) -> str:
    """Return a short SDK error message without request headers or secrets."""
    message = str(exc).replace("\n", " ").strip()
    if len(message) > 500:
        return f"{message[:500]}..."
    return message
