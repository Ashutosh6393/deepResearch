import re
import time
from uuid import uuid4

import structlog
from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from deepresearch.api.exception_handlers import handle_unexpected_error
from deepresearch.observability.logging import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

# Accept UUIDs and other bounded, URL/header-safe identifiers.
REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,128}$")


class RequestContextMiddleware:
    """
    Add request correlation and structured request logging.

    Incoming request IDs are accepted only when they match the
    allowed format. Otherwise, a new UUID is generated.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        incoming_request_id = headers.get(REQUEST_ID_HEADER)

        if incoming_request_id and REQUEST_ID_PATTERN.fullmatch(incoming_request_id):
            request_id = incoming_request_id
        else:
            request_id = str(uuid4())

        structlog.contextvars.clear_contextvars()
        context_tokens = structlog.contextvars.bind_contextvars(
            request_id=request_id,
        )
        start_time = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started

            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]

                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)

        except Exception as exc:
            logger.exception("request_failed")
            # ServerErrorMiddleware lives outside user middleware, so a
            # re-raised error would be rendered without this request ID.
            if response_started:
                raise
            response = await handle_unexpected_error(Request(scope), exc)
            await response(scope, receive, send_with_request_id)

        finally:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.info(
                "request_completed",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration_ms=duration_ms,
            )

            structlog.contextvars.reset_contextvars(**context_tokens)
