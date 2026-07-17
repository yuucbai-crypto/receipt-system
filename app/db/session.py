"""Database session management with SQLAlchemy async support."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_engine(settings: Settings) -> AsyncEngine:
    """Create async SQLAlchemy engine with SQLite WAL mode.

    Args:
        settings: Application settings

    Returns:
        AsyncEngine instance
    """
    # SQLite specific connect args for WAL mode and better concurrency
    connect_args = {
        "check_same_thread": False,
    }

    # For SQLite, we use NullPool to avoid connection pooling issues with async
    # WAL mode is enabled via PRAGMA in init_db
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args=connect_args,
        poolclass=NullPool,
        future=True,
    )

    logger.info(
        "Database engine created",
        extra={"extra_fields": {"database_url": settings.database_url}},
    )
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create async session factory.

    Args:
        engine: Async engine instance

    Returns:
        Async session factory
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@asynccontextmanager
async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """Get async database session context manager.

    Args:
        session_factory: Async session factory

    Yields:
        AsyncSession instance
    """
    async with session_factory() as session:
        # Enable foreign keys for each session
        await session.execute(text("PRAGMA foreign_keys=ON;"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session.

    Args:
        session_factory: Async session factory

    Yields:
        AsyncSession instance
    """
    async with get_session(session_factory) as session:
        yield session


async def close_engine(engine: AsyncEngine | None) -> None:
    """Close database engine connections.

    Args:
        engine: Async engine instance (or None)
    """
    if engine is not None:
        await engine.dispose()
        logger.info("Database engine closed")


def get_engine(settings: Settings) -> AsyncEngine:
    """Create and return a new engine instance.

    Note: This creates a new engine each call. For long-lived applications,
    prefer creating the engine once at startup and reusing it.

    Args:
        settings: Application settings

    Returns:
        AsyncEngine instance
    """
    return create_engine(settings)
