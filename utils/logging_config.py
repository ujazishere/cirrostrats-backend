import logging
import logging.config
import os
import sys
import uuid
from contextvars import ContextVar

try:
    # Prefer JSON formatter if available; fall back to basic
    from pythonjsonlogger import jsonlogger  # type: ignore
    _HAS_JSON = True
except Exception:
    _HAS_JSON = False


# Context variable to carry request-scoped values
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestContextFilter(logging.Filter):
    """Injects request_id and common fields into every log record."""

    def __init__(self, service: str, env: str) -> None:
        super().__init__()
        self.service = service
        self.env = env

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 (filter name required by logging)
        # Ensure stable fields exist on every record
        if not hasattr(record, "service"):
            record.service = self.service
        if not hasattr(record, "env"):
            record.env = self.env

        rid = request_id_ctx.get()
        if not hasattr(record, "request_id"):
            record.request_id = rid

        # Inject OpenTelemetry trace context for log-trace correlation
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span:
                ctx = span.get_span_context()
                if ctx and ctx.is_valid:
                    record.trace_id = format(ctx.trace_id, '032x')
                    record.span_id = format(ctx.span_id, '016x')
                else:
                    record.trace_id = None
                    record.span_id = None
            else:
                record.trace_id = None
                record.span_id = None
        except Exception:
            # If OpenTelemetry not available, set to None
            record.trace_id = None
            record.span_id = None

        # Placeholders to make downstream parsing stable
        for attr in ("http_method", "http_path", "status_code", "client_ip", "user_agent", "latency_ms"):
            if not hasattr(record, attr):
                setattr(record, attr, None)
        return True


def _json_formatter() -> dict:
    # Common JSON layout. Align keys to support downstream labels in Promtail/Loki.
    fmt = (
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "service=%(service)s env=%(env)s request_id=%(request_id)s "
        "trace_id=%(trace_id)s span_id=%(span_id)s "
        "http_method=%(http_method)s http_path=%(http_path)s status=%(status_code)s "
        "client_ip=%(client_ip)s user_agent=%(user_agent)s latency_ms=%(latency_ms)s"
    )
    return {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "fmt": fmt,
    }


def _plain_formatter() -> dict:
    return {
        "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                  " | svc=%(service)s env=%(env)s rid=%(request_id)s",
    }


def build_logging_config(service: str | None = None, env: str | None = None, level: str | None = None) -> dict:
    """Return a dictConfig for consistent, structured logging.

    - JSON if python-json-logger is installed; otherwise plain text.
    - Captures uvicorn and application loggers under the same handlers.
    """
    service_name = service or os.getenv("SERVICE_NAME", "cirrostrats-backend")
    environment = env or os.getenv("ENV", os.getenv("APP_ENV", "dev"))
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    # Allow forcing pretty console logs via env
    fmt_env = os.getenv("LOG_FORMAT", "").lower()
    if fmt_env in {"pretty", "plain", "console"}:
        formatter = _plain_formatter()
    else:
        formatter = _json_formatter() if _HAS_JSON else _plain_formatter()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": RequestContextFilter,
                "service": service_name,
                "env": environment,
            }
        },
        "formatters": {
            "structured": formatter,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "filters": ["request_context"],
                "formatter": "structured",
            }
        },
        "loggers": {
            # Uvicorn loggers
            "uvicorn": {"level": log_level, "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": log_level, "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": log_level, "handlers": ["console"], "propagate": False},
            # Celery loggers
            "celery": {"level": log_level, "handlers": ["console"], "propagate": False},
            # Root/app
            "": {"level": log_level, "handlers": ["console"]},
        },
    }


def setup_logging(service: str | None = None, env: str | None = None, level: str | None = None) -> None:
    """Apply structured logging configuration."""
    logging.config.dictConfig(build_logging_config(service=service, env=env, level=level))


def get_request_id() -> str:
    rid = request_id_ctx.get()
    return rid or ""


def set_request_id(value: str | None = None) -> str:
    rid = value or uuid.uuid4().hex
    request_id_ctx.set(rid)
    return rid
