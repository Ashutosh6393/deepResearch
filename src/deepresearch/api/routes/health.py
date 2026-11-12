
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from deepresearch.observability.logging import get_logger

router = APIRouter(prefix="/health", tags=["Health"])

logger = get_logger(__name__)


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """
    Check whether the application process is alive.

    This endpoint deliberately does not check external dependencies.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, str]:
    """
    Check whether the application is ready to serve requests.

    Currently checks database connectivity.
    """
    session_factory = request.app.state.session_factory

    try:
        async with session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar_one()

    except SQLAlchemyError:
        logger.exception("database_readiness_check_failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from None

    return {"status": "ok"}
