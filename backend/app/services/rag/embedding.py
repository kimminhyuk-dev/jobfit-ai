"""OpenAI 임베딩 생성 유틸리티."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from app.core.config import settings


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

logger = logging.getLogger(__name__)


class EmbeddingNotConfiguredError(Exception):
    """OpenAI API 키가 설정되지 않음"""


class EmbeddingGenerationError(Exception):
    """OpenAI 임베딩 생성 실패"""


def embed_texts(texts: list[str]) -> list[list[float]]:
    """text-embedding-3-small로 배치 임베딩. 키는 settings에서 로드."""

    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return []
    if not settings.openai_api_key:
        raise EmbeddingNotConfiguredError("OPENAI_API_KEY is not configured.")

    try:
        openai = importlib.import_module("openai")
    except ImportError as exc:  # pragma: no cover
        raise EmbeddingGenerationError("The openai package is not installed.") from exc

    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=clean_texts,
        )
    except Exception as exc:  # noqa: BLE001 - SDK 예외 타입은 버전별로 다르다.
        logger.warning(
            "OpenAI embedding call failed: %s: %s",
            exc.__class__.__name__,
            _safe_error_message(exc),
        )
        raise EmbeddingGenerationError("OpenAI embedding call failed.") from exc

    vectors = _extract_vectors(response)
    if len(vectors) != len(clean_texts):
        logger.warning(
            "OpenAI embedding count mismatch: expected=%s actual=%s",
            len(clean_texts),
            len(vectors),
        )
        raise EmbeddingGenerationError("OpenAI embedding count mismatch.")
    if any(len(vector) != EMBEDDING_DIMENSIONS for vector in vectors):
        raise EmbeddingGenerationError("OpenAI embedding dimension mismatch.")
    return vectors


def _extract_vectors(response: Any) -> list[list[float]]:
    data = sorted(getattr(response, "data", None) or [], key=lambda item: item.index)
    vectors: list[list[float]] = []
    for item in data:
        embedding = getattr(item, "embedding", None)
        if not isinstance(embedding, list):
            raise EmbeddingGenerationError("OpenAI embedding payload is invalid.")
        vectors.append([float(value) for value in embedding])
    return vectors


def _safe_error_message(exc: Exception) -> str:
    """요청 헤더나 키가 섞이지 않도록 짧은 오류 메시지만 남긴다."""

    message = str(exc).replace("\n", " ").strip()
    if len(message) > 500:
        return f"{message[:500]}..."
    return message
