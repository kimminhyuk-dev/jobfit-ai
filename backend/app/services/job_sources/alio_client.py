"""
ALIO 공공기관 채용정보 API client.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from app.core.config import settings


REQUEST_INTERVAL_SECONDS = 0.3
TIMEOUT_SECONDS = 30.0


class AlioClientError(Exception):
    """ALIO API 호출 실패"""


class AlioApiKeyMissingError(AlioClientError):
    """ALIO API 키 미설정"""


class AlioJsonParseError(AlioClientError):
    """ALIO JSON 파싱 실패"""


class AlioClient:
    """ALIO 채용정보 OpenAPI 동기 클라이언트."""

    def __init__(self) -> None:
        self.api_key = settings.alio_api_key
        self.list_url = settings.alio_recruit_list_url
        self.detail_url = settings.alio_recruit_detail_url

    def fetch_recruit_list(
        self,
        keyword: str | None = None,
        start_page: int = 1,
        display: int = 10,
    ) -> list[dict[str, Any]]:
        """채용정보 목록 API를 호출하고 내부 표준 dict 목록으로 반환한다."""
        self._ensure_api_key()
        params = {
            # TODO: ALIO 운영 가이드에서 인증키 파라미터명이 serviceKey 등으로
            # 다를 경우 이 키만 조정한다. 키 값은 예외/응답에 노출하지 않는다.
            "apiKey": self.api_key,
            "pageNo": start_page,
            "numOfRows": display,
            "type": "json",
        }
        if keyword:
            params["search"] = keyword

        payload = self._get_json(self.list_url, params)
        items = _extract_items(payload)
        return [_normalize_recruit(item) for item in items]

    def fetch_recruit_detail(self, source_job_id: str) -> dict[str, Any] | None:
        """채용정보 상세 API를 호출하고 내부 표준 dict로 반환한다."""
        self._ensure_api_key()
        params = {
            "apiKey": self.api_key,
            "recruit_id": source_job_id,
            "type": "json",
        }
        payload = self._get_json(self.detail_url, params)
        items = _extract_items(payload)
        if not items:
            return None
        return _normalize_recruit(items[0])

    def _get_json(self, url: str, params: dict[str, Any]) -> Any:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(url, params=params)
        if response.status_code >= 400:
            safe_url = _mask_api_key(str(response.request.url))
            raise AlioClientError(
                f"ALIO API 호출 실패: status={response.status_code}, url={safe_url}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise AlioJsonParseError("ALIO JSON 응답 파싱에 실패했습니다.") from exc

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise AlioApiKeyMissingError("ALIO API 키가 설정되지 않았습니다.")

    def wait_between_requests(self) -> None:
        """연속 페이지 호출 사이 최소 대기 시간을 보장한다."""
        time.sleep(REQUEST_INTERVAL_SECONDS)


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    """ALIO 응답 구조 차이에 방어적으로 대응해 item 목록을 추출한다."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise AlioJsonParseError("ALIO JSON 응답 형식이 올바르지 않습니다.")

    response = payload.get("response")
    body = response.get("body") if isinstance(response, dict) else None
    candidates: list[Any] = [
        payload.get("data"),
        payload.get("list"),
        payload.get("items"),
        payload.get("result"),
        body.get("items") if isinstance(body, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            nested = candidate.get("item") or candidate.get("items")
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
            if isinstance(nested, dict):
                return [nested]
    if _looks_like_recruit(payload):
        return [payload]
    return []


def _normalize_recruit(item: dict[str, Any]) -> dict[str, Any]:
    """ALIO 원본 필드를 내부 표준 dict로 변환한다."""
    source_job_id = _first_text(
        item,
        "recruit_id",
        "recruitId",
        "recruitNo",
        "recrutNo",
        "seq",
        "id",
        "sn",
    )

    # TODO: 실제 ALIO 코드 정의서의 상세 필드명을 확인한 뒤 alias를 좁힌다.
    normalized = {
        "source_job_id": source_job_id,
        "source_url": _first_text(item, "url", "sourceUrl", "recruitUrl"),
        "company_name": _first_text(item, "pname", "instNm", "orgNm", "companyName"),
        "title": _first_text(item, "title", "recruitTitle", "pbancTtl"),
        "location": _first_text(item, "locationNa", "location", "workRegionNm"),
        "location_code": _first_text(item, "location", "locationCd", "workRegionCd"),
        "career_level": _first_text(item, "carrerNa", "careerNa", "recruitTypeNm"),
        "career_level_code": _first_text(item, "careerCd", "recruitTypeCd"),
        "education": _first_text(item, "eduNa", "education", "educationNm"),
        "education_code": _first_text(item, "eduCd", "educationCd"),
        "employment_type": _first_text(item, "workTypeNa", "workType", "empTypeNm"),
        "employment_type_code": _first_text(item, "workType", "workTypeCd", "empTypeCd"),
        "ncs_category": _first_text(item, "ncsNa", "ncs", "detailCode"),
        "ncs_category_code": _first_text(item, "ncsCd", "ncsCode", "detailCodeCd"),
        "organization_type": _first_text(item, "orgTypeNa", "instTypeNm"),
        "organization_type_code": _first_text(item, "orgType", "instTypeCd"),
        "organization_category": _first_text(item, "instClsfNm", "orgCategoryNm"),
        "organization_category_code": _first_text(item, "instClsf", "orgCategoryCd"),
        "ministry": _first_text(item, "ministryNm", "mainDeptNm"),
        "ministry_code": _first_text(item, "ministryCd", "mainDeptCd"),
        "posted_at": _first_text(item, "termStart", "openDate", "regDate", "idate"),
        "deadline": _first_text(item, "termEnd", "closeDate", "endDate"),
        "updated_from_source_at": _first_text(item, "modDate", "updateDate"),
        "raw_content": _first_text(item, "contents", "content", "detail"),
        "parsed_skills": _split_keywords(_first_text(item, "keyword", "keywords")),
        "status": _normalize_status(_first_text(item, "status", "statusNm")),
        "raw_response": item,
    }
    if not normalized["source_url"] and source_job_id:
        normalized["source_url"] = f"https://job.alio.go.kr/recruitview.do?idx={source_job_id}"
    return normalized


def _first_text(data: dict[str, Any], *keys: str) -> str | None:
    lowered = {key.lower(): value for key, value in data.items()}
    for key in keys:
        value = data.get(key)
        if value is None:
            value = lowered.get(key.lower())
        text = _text_or_none(value)
        if text:
            return text
    return None


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _split_keywords(value: str | None) -> list[str] | None:
    if not value:
        return None
    keywords = [item.strip() for item in value.replace("|", ",").split(",")]
    return [item for item in keywords if item] or None


def _normalize_status(value: str | None) -> str:
    if not value:
        return "OPEN"
    if value in {"마감", "종료", "CLOSED", "close"}:
        return "CLOSED"
    return "OPEN"


def _looks_like_recruit(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in ("title", "pname", "recruit_id", "recruitId"))


def _mask_api_key(url: str) -> str:
    parts = urlsplit(url)
    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    masked_query = urlencode(
        [
            (key, "***" if key.lower() in {"apikey", "servicekey"} else value)
            for key, value in query_pairs
        ]
    )
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, masked_query, parts.fragment)
    )
