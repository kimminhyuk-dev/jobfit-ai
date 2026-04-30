"""
ALIO recruitment API client.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree

import httpx

from app.core.config import settings


RECRUIT_LIST_PATH = "/new/odaApiMng/recrutInquiryAjaxList.do"
RECRUIT_DETAIL_PATH = "/new/odaApiMng/recrutInquiryDetail.do"
LEGACY_RECRUIT_LIST_PATH = "/v1/recruit/list.do"
LEGACY_RECRUIT_DETAIL_PATH = "/v1/recruit/detail.do"
REQUEST_INTERVAL_SECONDS = 0.3
TIMEOUT_SECONDS = 30.0


class AlioClientError(Exception):
    """ALIO API call failed."""


class AlioApiKeyMissingError(AlioClientError):
    """ALIO API key is missing."""


class AlioJsonParseError(AlioClientError):
    """ALIO JSON/XML parsing failed."""


class AlioClient:
    """Client that normalizes ALIO recruitment responses."""

    def __init__(self) -> None:
        self.api_key = settings.alio_api_key
        self.base_url = settings.alio_base_url.rstrip("/")
        self.list_url = _resolve_list_url(
            base_url=self.base_url,
            legacy_url=settings.alio_recruit_list_url,
        )
        self.detail_url = _resolve_detail_url(
            base_url=self.base_url,
            legacy_url=settings.alio_recruit_detail_url,
        )

    def fetch_recruit_list(
        self,
        keyword: str | None = None,
        start_page: int = 1,
        display: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch a recruitment page and return normalized dicts."""
        self._ensure_api_key()
        if _uses_current_recruit_endpoint(self.list_url):
            params = {
                "pageNo": start_page,
                "numOfRows": display,
                "ongoingYn": "A",
            }
            if keyword:
                params["recrutPbancTtl"] = keyword
            payload = self._request_payload("POST", self.list_url, params)
        else:
            params = {
                "apiKey": self.api_key,
                "pageNo": start_page,
                "numOfRows": display,
                "type": "json",
            }
            if keyword:
                params["search"] = keyword
            payload = self._request_payload("GET", self.list_url, params)

        if _contains_api_error_payload(payload):
            raise AlioClientError("ALIO API returned an error payload.")
        items = _extract_items(payload)
        return [_normalize_recruit(item) for item in items]

    def fetch_recruit_detail(self, source_job_id: str) -> dict[str, Any] | None:
        """Fetch a recruitment detail response and return a normalized dict."""
        self._ensure_api_key()
        params = {
            "apiKey": self.api_key,
            "recruit_id": source_job_id,
            "type": "json",
        }
        payload = self._request_payload("GET", self.detail_url, params)
        if _contains_api_error_payload(payload):
            raise AlioClientError("ALIO detail API returned an error payload.")
        items = _extract_items(payload)
        if not items:
            return None
        return _normalize_recruit(items[0])

    def _request_payload(self, method: str, url: str, params: dict[str, Any]) -> Any:
        with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=False) as client:
            if method == "POST":
                response = client.post(url, data=params)
            else:
                response = client.get(url, params=params)

        if response.status_code >= 400:
            safe_url = _mask_api_key(str(response.request.url))
            raise AlioClientError(
                f"ALIO API call failed: status={response.status_code}, url={safe_url}"
            )
        if 300 <= response.status_code < 400:
            safe_url = _mask_api_key(str(response.request.url))
            safe_location = _mask_api_key(response.headers.get("location", ""))
            raise AlioClientError(
                "ALIO API call failed: "
                f"status={response.status_code}, url={safe_url}, location={safe_location}"
            )

        text = response.text.strip()
        if not text:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            try:
                return _xml_to_dict(text)
            except ElementTree.ParseError:
                content_type = response.headers.get("content-type", "")
                if "html" in content_type.lower() or text.lower().startswith("<!doctype html"):
                    raise AlioClientError(
                        "ALIO API returned HTML instead of JSON/XML."
                    ) from exc
                raise AlioJsonParseError("ALIO JSON/XML parsing failed.") from exc

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise AlioApiKeyMissingError("ALIO API key is missing.")

    def wait_between_requests(self) -> None:
        """Ensure a minimum delay between page requests."""
        time.sleep(REQUEST_INTERVAL_SECONDS)


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    """Extract item lists from known ALIO response envelopes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise AlioJsonParseError("ALIO response payload is not an object.")

    payload = _unwrap_single_root(payload)
    response = payload.get("response")
    body = response.get("body") if isinstance(response, dict) else None
    candidates: list[Any] = [
        payload.get("data"),
        payload.get("list"),
        payload.get("items"),
        payload.get("result"),
        payload.get("rows"),
        payload.get("row"),
        body.get("items") if isinstance(body, dict) else None,
        body.get("item") if isinstance(body, dict) else None,
    ]
    for candidate in candidates:
        items = _coerce_items(candidate)
        if items:
            return items

    items = _find_nested_items(payload)
    if items:
        return items
    if _looks_like_recruit(payload):
        return [payload]
    return []


def _normalize_recruit(item: dict[str, Any]) -> dict[str, Any]:
    """Map ALIO source fields to the app's job posting shape."""
    source_job_id = _first_text(
        item,
        "recruit_id",
        "recruitId",
        "recruitNo",
        "recrutNo",
        "recrutPblntSn",
        "seq",
        "id",
        "sn",
    )

    normalized = {
        "source_job_id": source_job_id,
        "source_url": _first_text(item, "url", "sourceUrl", "recruitUrl", "srcUrl"),
        "company_name": _first_text(item, "pname", "instNm", "orgNm", "companyName"),
        "title": _first_text(
            item,
            "title",
            "recruitTitle",
            "pbancTtl",
            "recrutPbancTtl",
        ),
        "location": _first_text(
            item,
            "locationNa",
            "location",
            "workRegionNm",
            "workRgnNmLst",
        ),
        "location_code": _first_text(
            item,
            "location",
            "locationCd",
            "workRegionCd",
            "workRgnLst",
        ),
        "career_level": _first_text(
            item,
            "carrerNa",
            "careerNa",
            "recruitTypeNm",
            "recrutSeNm",
        ),
        "career_level_code": _first_text(
            item,
            "careerCd",
            "recruitTypeCd",
            "recrutSe",
        ),
        "education": _first_text(
            item,
            "eduNa",
            "education",
            "educationNm",
            "acbgCondNmLst",
        ),
        "education_code": _first_text(
            item,
            "eduCd",
            "educationCd",
            "acbgCondLst",
        ),
        "employment_type": _first_text(
            item,
            "workTypeNa",
            "workType",
            "empTypeNm",
            "hireTypeNmLst",
        ),
        "employment_type_code": _first_text(
            item,
            "workType",
            "workTypeCd",
            "empTypeCd",
            "hireTypeLst",
        ),
        "ncs_category": _first_text(
            item,
            "ncsNa",
            "ncs",
            "detailCode",
            "ncsCdNmLst",
        ),
        "ncs_category_code": _first_text(
            item,
            "ncsCd",
            "ncsCode",
            "detailCodeCd",
            "ncsCdLst",
        ),
        "organization_type": _first_text(item, "orgTypeNa", "instTypeNm"),
        "organization_type_code": _first_text(item, "orgType", "instTypeCd"),
        "organization_category": _first_text(item, "instClsfNm", "orgCategoryNm"),
        "organization_category_code": _first_text(item, "instClsf", "orgCategoryCd"),
        "ministry": _first_text(item, "ministryNm", "mainDeptNm"),
        "ministry_code": _first_text(item, "ministryCd", "mainDeptCd"),
        "posted_at": _first_text(
            item,
            "termStart",
            "openDate",
            "regDate",
            "idate",
            "pbancBgngYmd",
        ),
        "deadline": _first_text(
            item,
            "termEnd",
            "closeDate",
            "endDate",
            "pbancEndYmd",
        ),
        "updated_from_source_at": _first_text(item, "modDate", "updateDate"),
        "raw_content": _first_text(item, "contents", "content", "detail", "aplyQlfcCn"),
        "parsed_skills": _split_keywords(_first_text(item, "keyword", "keywords")),
        "status": _normalize_status(_first_text(item, "status", "statusNm", "ongoingYn")),
        "raw_response": item,
    }
    if not normalized["source_url"] and source_job_id:
        normalized["source_url"] = (
            "https://opendata.alio.go.kr/new/odaApiMng/recrutInquiryDetail.do"
            f"?sn={source_job_id}"
        )
    return normalized


def _uses_current_recruit_endpoint(url: str) -> bool:
    return "recrutInquiryAjaxList.do" in url


def _resolve_list_url(base_url: str, legacy_url: str | None = None) -> str:
    default_url = _build_url(base_url, RECRUIT_LIST_PATH)
    if not legacy_url:
        return default_url
    if LEGACY_RECRUIT_LIST_PATH in legacy_url:
        return default_url
    if RECRUIT_LIST_PATH in legacy_url:
        return default_url
    return default_url


def _resolve_detail_url(base_url: str, legacy_url: str | None = None) -> str:
    default_url = _build_url(base_url, RECRUIT_DETAIL_PATH)
    if not legacy_url:
        return default_url
    if LEGACY_RECRUIT_DETAIL_PATH in legacy_url:
        return default_url
    if RECRUIT_DETAIL_PATH in legacy_url:
        return default_url
    return default_url


def _build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _unwrap_single_root(payload: dict[str, Any]) -> dict[str, Any]:
    if len(payload) != 1:
        return payload
    value = next(iter(payload.values()))
    if isinstance(value, dict):
        return value
    return payload


def _coerce_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        if _looks_like_recruit(value):
            return [value]
        for key in ("result", "item", "items", "list", "rows", "row"):
            items = _coerce_items(value.get(key))
            if items:
                return items
    return []


def _find_nested_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        items = _coerce_items(value)
        if items:
            return items
        for item in value.values():
            items = _find_nested_items(item)
            if items:
                return items
    if isinstance(value, list):
        for item in value:
            items = _find_nested_items(item)
            if items:
                return items
    return []


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
    normalized = value.strip().lower()
    if normalized in {"n", "closed", "close", "end", "ended", "마감", "종료"}:
        return "CLOSED"
    return "OPEN"


def _looks_like_recruit(payload: dict[str, Any]) -> bool:
    return any(
        key in payload
        for key in (
            "title",
            "pname",
            "recruit_id",
            "recruitId",
            "recrutPblntSn",
            "recrutPbancTtl",
        )
    )


def _contains_api_error_payload(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in {"errorcode", "resultcode"}:
                text = _scalar_text(item)
                if text and text.strip().lower() not in {
                    "0",
                    "00",
                    "0000",
                    "200",
                    "success",
                    "ok",
                }:
                    return True
            if _contains_api_error_payload(item):
                return True
    if isinstance(value, list):
        return any(_contains_api_error_payload(item) for item in value)
    return False


def _scalar_text(value: Any) -> str | None:
    if isinstance(value, dict):
        if len(value) != 1:
            return None
        return _scalar_text(next(iter(value.values())))
    if isinstance(value, list):
        return None
    return _text_or_none(value)


def _xml_to_dict(xml_text: str) -> dict[str, Any]:
    return _xml_element_to_dict(ElementTree.fromstring(xml_text))


def _xml_element_to_dict(element: ElementTree.Element) -> dict[str, Any]:
    children = list(element)
    if not children:
        return {element.tag: (element.text or "").strip()}

    result: dict[str, Any] = {}
    for child in children:
        child_dict = _xml_element_to_dict(child)
        key, value = next(iter(child_dict.items()))
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(value)
        else:
            result[key] = value
    return {element.tag: result}


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
