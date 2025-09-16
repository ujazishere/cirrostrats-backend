import logging
import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import set_request_id


class RequestContextLogMiddleware(BaseHTTPMiddleware):
    """Adds a request id and emits structured access logs.

    - Propagates `X-Request-ID` if provided by client; otherwise generates one.
    - Logs a single line per request with latency and key HTTP attributes.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = logging.getLogger("uvicorn.access")

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()

        # Bind request id
        req_id = request.headers.get("x-request-id")
        req_id = set_request_id(req_id)

        # Ensure response carries the request id
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            # Error path also logs an access event with 500
            self._log(request, status_code, start)
            raise

        # Attach the request id header for correlation
        response.headers["X-Request-ID"] = req_id

        # Access log
        self._log(request, status_code, start)
        return response

    def _log(self, request: Request, status_code: int, start_time: float) -> None:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Structured access log entry
        self.logger.info(
            "HTTP request",
            extra={
                "http_method": request.method,
                "http_path": request.url.path,
                "status_code": status_code,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "latency_ms": duration_ms,
            },
        )

