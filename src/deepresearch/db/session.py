from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from deepresearch.config import get_settings


def create_database_engine() -> AsyncEngine:
    """
    Create the asynchronous SQLAlchemy engine.

    Connection pooling is managed by SQLAlchemy.
    """
    settings = get_settings()

    return create_async_engine(
        settings.database_url.get_secret_value(),
        echo=False,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
        pool_pre_ping=True,
    )


engine = create_database_engine()

SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session.

    The session is closed automatically after the consumer finishes.

    Transaction boundaries are controlled by the application service,
    not implicitly committed by this dependency.
    """
    async with SessionFactory() as session:
        yield session


async def dispose_database_engine() -> None:
    """
    Close all connections in the SQLAlchemy connection pool.
    """
    await engine.dispose()
