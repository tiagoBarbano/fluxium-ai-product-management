from datetime import UTC, datetime
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .exceptions import ApplicationError
from ..observability.request_context import get_trace_id


logger = logging.getLogger(__name__)


def _problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    error_type: str = "about:blank",
) -> JSONResponse:
    payload = {
        "type": error_type,
        "title": title,
        "status": status_code,
        "detail": detail,
        "timestamp": datetime.now(UTC).isoformat(),
        "traceId": get_trace_id(),
    }
    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
        headers={"Trace-Id": get_trace_id()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_error(
        request: Request,
        exception: HTTPException,
    ) -> JSONResponse:
        detail = exception.detail
        if isinstance(detail, dict):
            detail = detail.get("message") or "The request could not be authorized."
        return _problem_response(
            request,
            status_code=exception.status_code,
            title="HTTP error",
            detail=str(detail),
        )

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request,
        exception: ApplicationError,
    ) -> JSONResponse:
        return _problem_response(
            request,
            status_code=exception.status_code,
            title=exception.title,
            detail=exception.detail,
            error_type=exception.error_type,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        return _problem_response(
            request,
            status_code=422,
            title="Validation error",
            detail="The request contains invalid fields.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exception: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exception)
        return _problem_response(
            request,
            status_code=500,
            title="Internal server error",
            detail="An unexpected error occurred.",
        )
