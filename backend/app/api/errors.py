"""Uniform error envelope used by every /api/* route.

Per API_CONTRACT.md §1.2, every non-2xx response body has the shape::

    {"error": "<machine_code>", "error_message": "<human readable>"}

The handlers registered in :func:`register_error_handlers` translate
FastAPI's default ``RequestValidationError`` and ``HTTPException`` into this
envelope so the frontend can rely on one renderer.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def error_response(
    status_code: int, error: str, error_message: str
) -> JSONResponse:
    """Build a JSONResponse matching the API_CONTRACT.md §1.2 envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "error_message": error_message},
    )


class APIError(HTTPException):
    """An :class:`HTTPException` carrying a machine code + human message.

    Routes raise these; the global handler unwraps and re-serializes them
    into the contract envelope.
    """

    def __init__(self, status_code: int, error: str, error_message: str) -> None:
        super().__init__(status_code=status_code, detail=error_message)
        self.error = error
        self.error_message = error_message


def _validation_message(exc: RequestValidationError) -> str:
    """Build a short human-readable message from Pydantic's error details."""
    errs = exc.errors()
    if not errs:
        return "Request body failed validation."
    first = errs[0]
    loc = ".".join(str(p) for p in first.get("loc", ()) if p != "body")
    msg = first.get("msg", "invalid value")
    if loc:
        return f"{loc}: {msg}"
    return msg


def register_error_handlers(app: FastAPI) -> None:
    """Register the global error handlers on a FastAPI app instance."""

    @app.exception_handler(APIError)
    async def _api_error_handler(_, exc: APIError) -> JSONResponse:  # type: ignore[misc]
        return error_response(exc.status_code, exc.error, exc.error_message)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(  # type: ignore[misc]
        _, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            status_code=422,
            error="validation_error",
            error_message=_validation_message(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(_, exc: StarletteHTTPException) -> JSONResponse:  # type: ignore[misc]
        # Map FastAPI/Starlette's default HTTPException into our envelope so
        # 404s on unknown routes also use the standard shape.
        code_map: dict[int, str] = {
            404: "not_found",
            405: "method_not_allowed",
            400: "bad_request",
        }
        code = code_map.get(exc.status_code, "http_error")
        detail = (
            exc.detail
            if isinstance(exc.detail, str)
            else f"{exc.status_code} {exc.__class__.__name__}"
        )
        return error_response(exc.status_code, code, detail)

    @app.exception_handler(Exception)
    async def _unhandled(_, exc: Exception) -> JSONResponse:  # type: ignore[misc]
        logger.exception("Unhandled exception in route")
        return error_response(
            status_code=500,
            error="internal_error",
            error_message="An unexpected error occurred.",
        )
