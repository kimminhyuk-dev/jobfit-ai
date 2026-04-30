"""
Work24 OpenAPI client.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree

import httpx

from app.core.config import settings


LIST_PATH = "/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"
DETAIL_PATH = "/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do"
REQUEST_INTERVAL_SECONDS = 0.3
TIMEOUT_SECONDS = 30.0
ERROR_FIELD_NAMES = {"errorcode", "resultcode", "code", "resultmsg", "message"}
ERROR_CODE_FIELD_NAMES = {"errorcode", "resultcode", "code"}
ERROR_MESSAGE_FIELD_NAMES = {"resultmsg", "message"}
SUCCESS_CODES = {"0", "00", "0000", "success", "ok", "y"}
ERROR_MESSAGE_KEYWORDS = ("오류", "에러", "권한", "제한", "실패", "error", "fail")


class Work24ClientError(Exception):
    """Work24 API 호출 실패"""


class Work24ApiKeyMissingError(Work24ClientError):
    """Work24 API 키 미설정"""


class Work24XmlParseError(Work24ClientError):
    """Work24 XML 파싱 실패"""


class Work24Client:
    """고용24 채용정보 OpenAPI 동기 클라이언트."""

    def __init__(self) -> None:
        self.base_url = settings.work24_base_url.rstrip("/")
        self.auth_key = settings.work24_job_api_key

    def fetch_job_list(
        self,
        keyword: str | None = None,
        start_page: int = 1,
        display: int = 10,
        region: str | list[str] | None = None,
        occupation: str | list[str] | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """채용정보 목록 API를 호출하고 정규화된 dict 목록으로 반환한다."""
        self._ensure_auth_key()
        params = {
            "authKey": self.auth_key,
            "callTp": "L",
            "returnType": "XML",
            "startPage": start_page,
            "display": display,
        }
        optional_params = {
            "keyword": keyword,
            "region": _join_multi_value(region),
            "occupation": _join_multi_value(occupation),
            **kwargs,
        }
        params.update(
            {key: value for key, value in optional_params.items() if value not in (None, "")}
        )

        xml_text = self._get(LIST_PATH, params)
        if not xml_text.strip():
            return []
        return self._parse_xml_to_list(xml_text)

    def fetch_job_detail(self, wanted_auth_no: str) -> dict[str, Any] | None:
        """
        채용정보 상세 API를 호출한다.

        TODO: Phase 2에서는 정의만 유지하고 수집 흐름에서는 호출하지 않는다.
        상세 응답의 jobCont는 raw_content, keywordList.srchKeywordNm은
        parsed_skills 매핑에 사용할 예정이다.
        """
        self._ensure_auth_key()
        params = {
            "authKey": self.auth_key,
            "wantedAuthNo": wanted_auth_no,
            "callTp": "D",
            "returnType": "XML",
            "infoSvc": "VALIDATION",
        }
        xml_text = self._get(DETAIL_PATH, params)
        if not xml_text.strip():
            return None
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as exc:
            raise Work24XmlParseError("Work24 상세 XML 파싱에 실패했습니다.") from exc
        if root is None or not list(root):
            return None
        detail = _element_to_dict(root)
        if _contains_api_error_payload(detail):
            raise Work24ClientError("Work24 상세 API가 오류 응답을 반환했습니다.")
        return detail

    def _parse_xml_to_list(self, xml_text: str) -> list[dict[str, Any]]:
        """Work24 목록 XML을 정규화된 채용공고 dict 목록으로 변환한다."""
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as exc:
            raise Work24XmlParseError("Work24 목록 XML 파싱에 실패했습니다.") from exc

        payload = _element_to_dict(root)
        if _contains_api_error_payload(payload):
            raise Work24ClientError("Work24 목록 API가 오류 응답을 반환했습니다.")

        wanted_nodes = root.findall(".//wanted")
        return [_normalize_wanted(_element_to_dict(node)) for node in wanted_nodes]

    def _get(self, path: str, params: dict[str, Any]) -> str:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(url, params=params)
        if response.status_code >= 400:
            safe_url = self._mask_auth_key(str(response.request.url))
            raise Work24ClientError(
                f"Work24 API 호출 실패: status={response.status_code}, url={safe_url}"
            )
        return response.text

    def _ensure_auth_key(self) -> None:
        if not self.auth_key:
            raise Work24ApiKeyMissingError("Work24 채용정보 API 키가 설정되지 않았습니다.")

    def _mask_auth_key(self, url: str) -> str:
        """authKey 쿼리 파라미터 값을 로그/예외 메시지용으로 마스킹한다."""
        parts = urlsplit(url)
        query_pairs = parse_qsl(parts.query, keep_blank_values=True)
        masked_query = urlencode(
            [(key, "***" if key == "authKey" else value) for key, value in query_pairs]
        )
        return urlunsplit((parts.scheme, parts.netloc, parts.path, masked_query, parts.fragment))

    def wait_between_requests(self) -> None:
        """연속 페이지 호출 사이 최소 대기 시간을 보장한다."""
        time.sleep(REQUEST_INTERVAL_SECONDS)


def _parse_xml_to_list(xml_text: str) -> list[dict[str, Any]]:
    """테스트/내부 재사용용 모듈 헬퍼."""
    return Work24Client()._parse_xml_to_list(xml_text)


def _mask_auth_key(url: str) -> str:
    """테스트/내부 재사용용 모듈 헬퍼."""
    return Work24Client()._mask_auth_key(url)


def _join_multi_value(value: str | list[str] | None) -> str | None:
    if isinstance(value, list):
        return "|".join(item for item in value if item)
    return value


def _element_to_dict(element: ElementTree.Element) -> dict[str, Any]:
    children = list(element)
    if not children:
        return {element.tag: (element.text or "").strip()}

    result: dict[str, Any] = {}
    for child in children:
        child_dict = _element_to_dict(child)
        key, value = next(iter(child_dict.items()))
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(value)
        else:
            result[key] = value
    return result


def _normalize_wanted(wanted: dict[str, Any]) -> dict[str, Any]:
    basic_address = _get_text(wanted, "basicAddr")
    detail_address = _get_text(wanted, "detailAddr")
    location_address = (
        f"{basic_address} {detail_address}" if basic_address and detail_address else None
    )

    return {
        "source_job_id": _get_text(wanted, "wantedAuthNo"),
        "company_name": _get_text(wanted, "company"),
        "business_number": _get_text(wanted, "busino"),
        "industry": _get_text(wanted, "indTpNm"),
        "title": _get_text(wanted, "title"),
        "location": _get_text(wanted, "region"),
        "location_address": location_address,
        "career_level": _get_text(wanted, "career"),
        "education": _get_text(wanted, "minEdubg"),
        "employment_type_code": _get_text(wanted, "empTpCd"),
        "work_schedule": _get_text(wanted, "holidayTpNm"),
        "salary_type": _get_text(wanted, "salTpNm"),
        "salary_text": _get_text(wanted, "sal"),
        "min_salary": _get_text(wanted, "minSal"),
        "max_salary": _get_text(wanted, "maxSal"),
        "posted_at": _get_text(wanted, "regDt"),
        "deadline": _get_text(wanted, "closeDt"),
        "source_updated_at": _get_text(wanted, "smodifyDtm"),
        "source_url": _get_text(wanted, "wantedInfoUrl"),
        "mobile_url": _get_text(wanted, "wantedMobileInfoUrl"),
        "raw_response": wanted,
    }


def _contains_api_error_payload(value: Any) -> bool:
    """권한/오류 응답을 정상 채용공고 데이터로 해석하지 않도록 감지한다."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in ERROR_FIELD_NAMES and _is_error_field(
                normalized_key,
                item,
            ):
                return True
            if _contains_api_error_payload(item):
                return True
    if isinstance(value, list):
        return any(_contains_api_error_payload(item) for item in value)
    return False


def _is_error_field(key: str, value: Any) -> bool:
    text = _get_scalar_text(value)
    if text is None:
        return False
    normalized = text.strip().lower()
    if key in ERROR_CODE_FIELD_NAMES:
        return normalized not in SUCCESS_CODES
    if key in ERROR_MESSAGE_FIELD_NAMES:
        return any(keyword in normalized for keyword in ERROR_MESSAGE_KEYWORDS)
    return False


def _get_scalar_text(value: Any) -> str | None:
    if isinstance(value, dict):
        if len(value) != 1:
            return None
        return _get_scalar_text(next(iter(value.values())))
    if isinstance(value, list):
        return None
    return _get_text({"value": value}, "value")


def _get_text(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None
