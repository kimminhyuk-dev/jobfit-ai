"""
Application exception types.
"""

from app.core.error_codes import ErrorCode


class AppException(Exception):
    """Exception carrying an API error code and client-facing message."""

    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers
        super().__init__(message)
