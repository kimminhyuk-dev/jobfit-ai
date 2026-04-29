"""
FastAPI exception handlers for consistent API error responses.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCode.VALIDATION_ERROR,
            message="요청 값이 올바르지 않습니다.",
            details=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code = ErrorCode.NOT_FOUND
        message = "요청한 리소스를 찾을 수 없습니다."

        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = ErrorCode.UNAUTHORIZED
            message = "인증 정보가 유효하지 않습니다."
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = ErrorCode.FORBIDDEN
            message = "접근 권한이 없습니다."
        elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = ErrorCode.METHOD_NOT_ALLOWED
            message = "허용되지 않은 요청 방식입니다."
        elif exc.status_code != status.HTTP_404_NOT_FOUND:
            code = ErrorCode.INTERNAL_SERVER_ERROR
            message = "요청 처리 중 오류가 발생했습니다."

        if isinstance(exc.detail, str) and exc.detail not in {
            "Not Found",
            "Method Not Allowed",
        }:
            message = exc.detail
        elif isinstance(exc.detail, dict):
            detail_code = exc.detail.get("code")
            detail_message = exc.detail.get("message")
            if detail_code:
                code = detail_code
            if detail_message:
                message = detail_message

        return _error_response(
            status_code=exc.status_code,
            code=code,
            message=message,
            headers=getattr(exc, "headers", None),
        )


def _error_response(
    status_code: int,
    code: ErrorCode | str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "code": str(code),
        "message": message,
    }
    if details is not None:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content, headers=headers)
