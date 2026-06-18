"""
면접 안내 메일 발송 서비스.

기업회원이 지원자에게 면접 일정/장소를 메일로 보낸다. 면접 장소 주소는
Google Maps Static API로 지도 이미지를 받아 **메일에 인라인(CID)으로 첨부**한다.

지도 처리 방식(공식 문서 기준):
- `<img src="...staticmap?...&key=KEY">` 를 메일에 직접 넣지 않는다.
  (API 키가 메일 소스에 노출되고, 다수 메일 클라이언트가 외부 이미지를 차단함)
- 대신 서버가 Static API에 요청해 PNG 바이트를 받아 인라인 첨부하고,
  추가로 Google Maps 길찾기 링크를 텍스트/버튼으로 병행한다.
- API 키는 settings 에서만 로드하며 메일 본문/링크에 노출하지 않는다.

지도 이미지를 받지 못해도(키 미설정/요청 실패) 메일은 정상 발송되며,
지도 링크는 그대로 포함한다(그레이스풀 디그레이데이션).
"""

from __future__ import annotations

import logging
from datetime import datetime
from html import escape
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.services.email_service import EmailService, build_transactional_email_html

logger = logging.getLogger(__name__)

_MAP_CID = "interview_map"
_MAP_TIMEOUT_SECONDS = 10.0


class InterviewEmailService:
    """면접 안내 메일을 구성하고 발송한다."""

    def __init__(self) -> None:
        self.email_service = EmailService()
        self.api_key = settings.google_maps_api_key
        self.static_base_url = settings.google_maps_static_base_url
        self.app_name = settings.app_name

    def _fetch_map_png(self, address: str) -> bytes | None:
        """면접 장소 주소로 Static Map PNG 바이트를 받아온다(실패 시 None)."""
        if not self.api_key or not address:
            return None
        params = {
            "center": address,
            "zoom": "16",
            "size": "600x300",
            "scale": "2",
            "markers": f"color:red|{address}",
            "key": self.api_key,
        }
        try:
            with httpx.Client(timeout=_MAP_TIMEOUT_SECONDS) as client:
                response = client.get(self.static_base_url, params=params)
            if response.status_code >= 400:
                logger.warning(
                    "Static Map 요청 실패: status=%s", response.status_code
                )
                return None
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image"):
                logger.warning("Static Map 응답이 이미지가 아님: %s", content_type)
                return None
            return response.content
        except httpx.HTTPError as exc:
            logger.warning("Static Map 요청 오류: error_type=%s", type(exc).__name__)
            return None

    @staticmethod
    def _maps_link(address: str) -> str:
        """Google Maps 검색 링크 (키 불필요)."""
        return f"https://www.google.com/maps/search/?api=1&query={quote(address)}"

    def send_interview_invitation(
        self,
        *,
        to: str,
        applicant_name: str | None,
        company_name: str | None,
        job_title: str | None,
        location_address: str,
        interview_at: datetime,
        message: str | None,
    ) -> bool:
        """면접 안내 메일을 발송한다. 반환값은 지도 이미지 첨부 성공 여부."""
        greeting_name = applicant_name or "지원자"
        company_label = company_name or self.app_name
        job_label = job_title or "채용 공고"
        when_text = interview_at.strftime("%Y-%m-%d %H:%M")
        maps_link = self._maps_link(location_address) if location_address else None

        map_png = self._fetch_map_png(location_address)
        inline_images = {_MAP_CID: map_png} if map_png else None

        subject = f"[{company_label}] 면접 안내 - {job_label}"

        # 평문 본문
        plain_lines = [
            self.app_name,
            "",
            "면접 안내",
            "",
            f"{greeting_name}님, 안녕하세요.",
            f"{company_label}의 '{job_label}' 면접 일정을 안내드립니다.",
            "",
            f"면접 일정 및 장소: {when_text} / {location_address or '(별도 안내)'}",
            "",
            f"지원 공고: {job_label}",
            f"회사명: {company_label}",
        ]
        if maps_link:
            plain_lines.append(f"지도: {maps_link}")
        if message:
            plain_lines += ["", message]
        plain_lines += [
            "",
            f"감사합니다.\n{company_label} 드림",
            "",
            "본 메일은 발신 전용으로 자동 발송되었습니다.",
            "본인이 요청하지 않았다면 이 메일을 무시해 주세요.",
        ]
        body = "\n".join(plain_lines)

        # HTML 본문
        map_block = ""
        if map_png:
            map_block = (
                '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                'style="width:100%;margin:8px 0 0 0;">'
                '<tr><td style="padding:0;">'
                f'<img src="cid:{_MAP_CID}" alt="면접 장소 지도" '
                'style="display:block;width:100%;max-width:544px;border:1px solid #e5e7eb;border-radius:10px;">'
                "</td></tr></table>"
            )
        link_block = ""
        if maps_link:
            link_block = (
                '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                'style="width:100%;margin:12px 0 0 0;">'
                "<tr><td>"
                f'<a href="{escape(maps_link)}" '
                'style="display:inline-block;padding:10px 16px;background-color:#1d4ed8;'
                'color:#ffffff;text-decoration:none;border-radius:8px;font-size:13px;font-weight:700;">'
                "지도에서 보기</a>"
                "</td></tr></table>"
            )
        message_block = (
            (
                '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                'style="width:100%;margin:14px 0 0 0;background-color:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;">'
                '<tr><td style="padding:14px 16px;font-size:14px;line-height:1.7;color:#374151;white-space:pre-line;">'
                f"{escape(message)}"
                "</td></tr></table>"
            )
            if message
            else ""
        )
        html = build_transactional_email_html(
            app_name=self.app_name,
            title="면접 안내",
            intro=f"{greeting_name}님, {company_label}의 면접 일정을 안내드립니다.",
            highlight_label="면접 일정 및 장소",
            highlight_value=f"{when_text} · {location_address or '(별도 안내)'}",
            helper_lines=[
                f"지원 공고: {job_label}",
                f"회사명: {company_label}",
            ],
            highlight_font_size="18px",
            extra_html=map_block + link_block + message_block,
        )

        self.email_service.send_email(
            to=to,
            subject=subject,
            body=body,
            html=html,
            inline_images=inline_images,
        )
        return map_png is not None
