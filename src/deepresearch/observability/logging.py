
import logging
import sys
from typing import Any

import structlog

from deepresearch.config import Environment, Settings, get_settings


def configure_logging(settings: Settings | None = None) -> None:
    """
    Configure application-wide structured logging.

    Development and testing use human-readable or JSON output
    respectively. Production uses JSON output.

    Must be called once during application startup, before
    application loggers are first used.
    """
    settings = settings or get_settings()

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.environment == Environment.DEVELOPMENT:
        renderer = structlog.dev.ConsoleRenderer(
            colors=sys.stdout.isatty(),
        )
    else:
        renderer = structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=settings.log_level,
        handlers=[handler],
        force=True,
    )

    # Route third-party logs through the application formatter.
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
    ):
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.handlers.clear()
        third_party_logger.propagate = True

    # Avoid logging raw SQL statements, parameters and access paths.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a structured application logger."""
    return structlog.get_logger(name)
