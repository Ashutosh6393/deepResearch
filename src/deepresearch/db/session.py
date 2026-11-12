
import asyncio
import sys
from collections.abc import AsyncIterator

from fastapi import Request

# psycopg async cannot run on the Windows ProactorEventLoop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from deepresearch.config import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine."""

    return create_async_engine(
        settings.database_url.get_secret_value(),
        echo=False,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
        pool_pre_ping=True,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create the application's asynchronous session factory."""

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_db_session(
    request: Request,
) -> AsyncIterator[AsyncSession]:
    """
    Provide a database session for the duration of a request.

    Transaction boundaries remain the responsibility of the
    application service or unit of work.
    """

    session_factory = request.app.state.session_factory

    async with session_factory() as session:
        yield session
