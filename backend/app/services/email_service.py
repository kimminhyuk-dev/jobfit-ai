"""
이메일 발송 서비스 (SMTP).

Spring JobFolio의 `JavaMailSender` 구조를 Python으로 이식한 모듈.

의존성 결정:
- 단순 동기 발송이면 충분하고 `aiosmtplib`가 설치되어 있지 않으므로,
  새 외부 의존성을 추가하지 않고 표준 라이브러리 `smtplib`/`email`/`ssl`을 사용한다.
  (비동기 대량 발송이 필요해지면 그때 `aiosmtplib` 도입을 검토한다.)

설정값은 전부 `app.core.config.settings`에서 읽는다.
- Spring 스타일 키(`spring.mail.*`)나 `os.getenv("spring.mail.host")`는 사용하지 않는다.
- 모든 키는 Python 스타일(`SMTP_HOST` → `settings.smtp_host`)로 접근한다.

보안:
- 실제 비밀번호, 인증코드, 임시 비밀번호 원문은 로그에 남기지 않는다.
- 로그에는 마스킹된 username과 `password loaded: true|false`만 남긴다.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from html import escape

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailConfigError(RuntimeError):
    """SMTP 설정이 누락되어 메일을 보낼 수 없는 상태."""


class EmailSendError(RuntimeError):
    """SMTP 발송 단계에서 실패한 상태."""


def _mask_username(username: str | None) -> str:
    """로그용 username 마스킹. 예: johndoe@gmail.com -> j***@gmail.com"""
    if not username:
        return "(none)"
    if "@" not in username:
        return username[:1] + "***"
    local, _, domain = username.partition("@")
    masked_local = (local[:1] + "***") if local else "***"
    return f"{masked_local}@{domain}"


def _build_plain_template(
    *,
    app_name: str,
    title: str,
    intro: str,
    highlight_label: str,
    highlight_value: str,
    helper_lines: list[str],
) -> str:
    lines = [
        app_name,
        "",
        title,
        "",
        intro,
        "",
        f"{highlight_label}: {highlight_value}",
        "",
        *helper_lines,
        "",
        "본 메일은 발신 전용으로 자동 발송되었습니다.",
        "본인이 요청하지 않았다면 이 메일을 무시해 주세요.",
    ]
    return "\n".join(line for line in lines if line is not None)


def build_transactional_email_html(
    *,
    app_name: str,
    title: str,
    intro: str,
    highlight_label: str,
    highlight_value: str,
    helper_lines: list[str],
    highlight_font_size: str = "22px",
    extra_html: str = "",
) -> str:
    """이메일 클라이언트 호환성을 위해 table + inline style만 사용하는 HTML 템플릿."""
    helper_rows = "".join(
        (
            '<tr>'
            '<td style="padding:0 0 8px 0;font-size:14px;line-height:1.7;color:#525252;">'
            f"{escape(line)}"
            "</td>"
            "</tr>"
        )
        for line in helper_lines
    )
    safe_extra_html = extra_html or ""
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background-color:#f6f8fb;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background-color:#f6f8fb;margin:0;padding:0;">
      <tr>
        <td align="center" style="padding:32px 16px;">
          <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
            <tr>
              <td style="padding:22px 28px;background-color:#1d4ed8;color:#ffffff;font-family:Arial,'Malgun Gothic',sans-serif;">
                <div style="font-size:18px;font-weight:700;line-height:1.3;">{escape(app_name)}</div>
                <div style="padding-top:4px;font-size:12px;line-height:1.5;color:#dbeafe;">AI 기반 이력서-채용공고 매칭 플랫폼</div>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 28px 10px 28px;font-family:Arial,'Malgun Gothic',sans-serif;color:#111827;">
                <h1 style="margin:0;font-size:22px;line-height:1.4;font-weight:700;color:#111827;">{escape(title)}</h1>
                <p style="margin:12px 0 0 0;font-size:14px;line-height:1.7;color:#525252;">{escape(intro)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:12px 28px 18px 28px;font-family:Arial,'Malgun Gothic',sans-serif;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;background-color:#eef4ff;border:1px solid #bfdbfe;border-radius:10px;">
                  <tr>
                    <td style="padding:20px 22px;text-align:center;">
                      <div style="font-size:13px;font-weight:700;line-height:1.5;color:#1d4ed8;">{escape(highlight_label)}</div>
                      <div style="padding-top:8px;font-size:{highlight_font_size};font-weight:800;line-height:1.4;color:#0a0a0a;letter-spacing:0;">{escape(highlight_value)}</div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 22px 28px;font-family:Arial,'Malgun Gothic',sans-serif;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;">
                  {helper_rows}
                </table>
                {safe_extra_html}
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px;background-color:#f9fafb;border-top:1px solid #e5e7eb;font-family:Arial,'Malgun Gothic',sans-serif;">
                <p style="margin:0;font-size:12px;line-height:1.7;color:#6b7280;">본 메일은 발신 전용으로 자동 발송되었습니다.</p>
                <p style="margin:4px 0 0 0;font-size:12px;line-height:1.7;color:#6b7280;">본인이 요청하지 않았다면 이 메일을 무시해 주세요.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


class EmailService:
    """SMTP 기반 메일 발송 서비스."""

    def __init__(self) -> None:
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.use_auth = settings.smtp_auth
        self.use_tls = settings.smtp_use_tls
        self.require_tls = settings.smtp_require_tls
        # Spring은 타임아웃을 밀리초로 받지만, smtplib 소켓 timeout은 초 단위다.
        self.timeout_seconds = max(settings.smtp_connection_timeout_ms, 1000) / 1000.0
        self.app_name = settings.app_name

    def is_configured(self) -> bool:
        """발송 가능한 최소 설정(host/username/password)이 있는지 확인."""
        return bool(self.host and self.username and self.password)

    def log_config(self) -> None:
        """설정 로딩 상태를 비밀번호 노출 없이 로그로 남긴다."""
        logger.info(
            "SMTP config loaded: host=%s, port=%s, username=%s",
            self.host or "(none)",
            self.port,
            _mask_username(self.username),
        )
        logger.info("SMTP password loaded: %s", bool(self.password))

    def _from_header(self) -> str:
        """발신자 표시명에 APP_NAME을 사용한다."""
        return formataddr((self.app_name, self.username or ""))

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
        inline_images: dict[str, bytes] | None = None,
    ) -> None:
        """
        공통 메일 발송.

        - `body`: 평문 본문(필수).
        - `html`: HTML 본문(선택). 있으면 multipart/alternative로 함께 보낸다.
        - `inline_images`: {cid: png_bytes} 형태. HTML에서 `cid:<키>` 로 참조하는
          인라인 이미지(예: 지도)를 multipart/related로 첨부한다. 외부 URL이 아니라
          메일 자체에 이미지를 넣으므로 API 키가 메일에 노출되지 않는다.
        """
        if not self.is_configured():
            raise EmailConfigError(
                "SMTP 설정이 비어 있습니다. .env의 SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD를 확인하세요."
            )

        message = EmailMessage()
        message["From"] = self._from_header()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        if html:
            message.add_alternative(html, subtype="html")
            if inline_images:
                # 마지막 파트(=HTML 대안)에 이미지를 related 로 붙인다.
                html_part = message.get_payload()[-1]
                for cid, image_bytes in inline_images.items():
                    html_part.add_related(
                        image_bytes,
                        maintype="image",
                        subtype="png",
                        cid=f"<{cid}>",
                    )

        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as server:
                server.ehlo()
                if self.use_tls:
                    if server.has_extn("starttls"):
                        server.starttls()
                        server.ehlo()
                    elif self.require_tls:
                        raise EmailSendError(
                            "서버가 STARTTLS를 지원하지 않지만 SMTP_REQUIRE_TLS=true 입니다."
                        )
                if self.use_auth:
                    server.login(self.username, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            # 예외 메시지에 자격증명이 들어가지 않도록 타입/대상만 로깅한다.
            logger.error(
                "SMTP send failed: to=%s, host=%s, error_type=%s",
                _mask_username(to),
                self.host,
                type(exc).__name__,
            )
            raise EmailSendError("메일 발송에 실패했습니다.") from exc

        logger.info("SMTP send ok: to=%s, subject=%s", _mask_username(to), subject)

    def send_verification_code(self, to: str, code: str) -> None:
        """비밀번호 재설정 인증 코드 발송. 코드 원문은 로그에 남기지 않는다."""
        subject = f"[{self.app_name}] 비밀번호 재설정 인증 코드"
        helper_lines = [
            "인증 코드는 5분 동안만 유효합니다.",
            "입력 화면에 6자리 숫자를 그대로 입력해 주세요.",
        ]
        body = _build_plain_template(
            app_name=self.app_name,
            title="비밀번호 재설정 인증 코드",
            intro="비밀번호 재설정을 계속하려면 아래 인증 코드를 입력해 주세요.",
            highlight_label="인증 코드",
            highlight_value=code,
            helper_lines=helper_lines,
        )
        html = build_transactional_email_html(
            app_name=self.app_name,
            title="비밀번호 재설정 인증 코드",
            intro="비밀번호 재설정을 계속하려면 아래 인증 코드를 입력해 주세요.",
            highlight_label="인증 코드",
            highlight_value=code,
            helper_lines=helper_lines,
            highlight_font_size="32px",
        )
        self.send_email(to=to, subject=subject, body=body, html=html)

    def send_temporary_password(self, to: str, temporary_password: str) -> None:
        """비밀번호 재설정용 임시 비밀번호 발송. 임시 비밀번호 원문은 로그에 남기지 않는다."""
        subject = f"[{self.app_name}] 임시 비밀번호 안내"
        helper_lines = [
            "로그인 후 즉시 새 비밀번호로 변경해 주세요.",
            "임시 비밀번호는 다른 사람에게 공유하지 마세요.",
        ]
        body = _build_plain_template(
            app_name=self.app_name,
            title="임시 비밀번호 안내",
            intro="인증이 완료되어 임시 비밀번호가 발급되었습니다.",
            highlight_label="임시 비밀번호",
            highlight_value=temporary_password,
            helper_lines=helper_lines,
        )
        html = build_transactional_email_html(
            app_name=self.app_name,
            title="임시 비밀번호 안내",
            intro="인증이 완료되어 임시 비밀번호가 발급되었습니다.",
            highlight_label="임시 비밀번호",
            highlight_value=temporary_password,
            helper_lines=helper_lines,
            highlight_font_size="24px",
        )
        self.send_email(to=to, subject=subject, body=body, html=html)

    def send_found_id_email(
        self,
        to: str,
        found_email: str,
        reg_date: str | None = None,
    ) -> None:
        """아이디(가입 이메일) 찾기 결과를 본인 메일로 발송한다."""
        subject = f"[{self.app_name}] 가입하신 아이디 안내"
        helper_lines = [
            "로그인 화면에서 위 이메일 주소를 아이디로 입력해 주세요.",
        ]
        if reg_date:
            helper_lines.append(f"가입일: {reg_date}")
        body = _build_plain_template(
            app_name=self.app_name,
            title="가입하신 아이디 안내",
            intro="요청하신 아이디 찾기 결과를 안내드립니다.",
            highlight_label="가입 이메일 주소",
            highlight_value=found_email,
            helper_lines=helper_lines,
        )
        html = build_transactional_email_html(
            app_name=self.app_name,
            title="가입하신 아이디 안내",
            intro="요청하신 아이디 찾기 결과를 안내드립니다.",
            highlight_label="가입 이메일 주소",
            highlight_value=found_email,
            helper_lines=helper_lines,
            highlight_font_size="22px",
        )
        self.send_email(to=to, subject=subject, body=body, html=html)


def get_email_service() -> EmailService:
    """FastAPI 의존성 주입용 팩토리."""
    return EmailService()
