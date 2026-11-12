
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from deepresearch.exceptions import ApplicationError
from deepresearch.observability.logging import get_logger

logger = get_logger(__name__)


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Build a consistent API error response."""

    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if details is not None:
        error["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
    )


async def handle_application_error(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """Convert expected application errors into HTTP responses."""

    logger.warning(
        "application_error",
        error_code=exc.code,
        status_code=exc.status_code,
    )

    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )


async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Convert request validation errors into a safe API response.

    Do not return raw input values. They may contain credentials,
    tokens, or other sensitive information.
    """

    details = [
        {
            "location": list(error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        details=details,
    )


async def handle_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected errors without exposing internal details."""

    logger.exception("unhandled_application_exception")

    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
