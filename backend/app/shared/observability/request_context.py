from contextvars import ContextVar
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request
from starlette.responses import Response


_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def get_correlation_id() -> str:
    return _correlation_id.get()


def get_trace_id() -> str:
    return _trace_id.get()


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    correlation_id = request.headers.get("Correlation-Id") or str(uuid4())
    trace_id = request.headers.get("Trace-Id") or str(uuid4())
    correlation_token = _correlation_id.set(correlation_id)
    trace_token = _trace_id.set(trace_id)
    try:
        response = await call_next(request)
        response.headers["Correlation-Id"] = correlation_id
        response.headers["Trace-Id"] = trace_id
        return response
    finally:
        _correlation_id.reset(correlation_token)
        _trace_id.reset(trace_token)
