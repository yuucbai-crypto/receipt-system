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

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global engine and session factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine() -> AsyncEngine:
    """Create async SQLAlchemy engine with SQLite WAL mode."""
    global _engine

    if _engine is not None:
        return _engine

    # SQLite specific connect args for WAL mode and better concurrency
    connect_args = {
        "check_same_thread": False,
    }

    # For SQLite, we use NullPool to avoid connection pooling issues with async
    # WAL mode is enabled via PRAGMA in init_db
    _engine = create_async_engine(
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
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create async session factory."""
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    engine = create_engine()
    _session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session context manager."""
    session_factory = get_session_factory()
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


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with get_session() as session:
        yield session


async def close_engine() -> None:
    """Close database engine connections."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")


def get_engine() -> AsyncEngine:
    """Get the global engine instance."""
    if _engine is None:
        return create_engine()
    return _engine
