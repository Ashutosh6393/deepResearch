from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.types import HTTPExceptionHandler

from deepresearch.api.exception_handlers import (
    handle_application_error,
    handle_unexpected_error,
    handle_validation_error,
)
from deepresearch.api.middleware import RequestContextMiddleware
from deepresearch.api.routes.health import router as health_router
from deepresearch.config import Settings, get_settings
from deepresearch.db.session import (
    create_database_engine,
    create_session_factory,
)
from deepresearch.exceptions import ApplicationError
from deepresearch.observability.logging import (
    configure_logging,
    get_logger,
)

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings)

        logger.info("application_starting")

        engine = create_database_engine(settings)

        try:
            app.state.engine = engine
            app.state.session_factory = create_session_factory(engine)

            yield

        finally:
            logger.info("application_shutting_down")

            await engine.dispose()

            logger.info("database_engine_disposed")

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(health_router)

    app.add_exception_handler(
        ApplicationError,
        cast(HTTPExceptionHandler, handle_application_error),
    )

    app.add_exception_handler(
        RequestValidationError,
        cast(HTTPExceptionHandler, handle_validation_error),
    )

    app.add_exception_handler(
        Exception,
        handle_unexpected_error,
    )

    app.add_middleware(RequestContextMiddleware)

    return app


app = create_app()
