"""Database initialization and schema creation."""

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import create_engine, get_engine
from app.models.base import Base

logger = get_logger(__name__)


async def init_db(engine: AsyncEngine | None = None) -> None:
    """Initialize database: enable WAL mode, create tables."""
    if engine is None:
        engine = get_engine()

    # Enable WAL mode for SQLite (better concurrency)
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA busy_timeout=5000;"))
        await conn.execute(text("PRAGMA foreign_keys=ON;"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info(
        "Database initialized",
        extra={"extra_fields": {"database_url": settings.database_url}},
    )


async def init_db_from_config() -> None:
    """Initialize database using settings configuration."""
    # Ensure data directory exists for SQLite file
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine()
    await init_db(engine)


async def close_db() -> None:
    """Close database connections."""
    from app.db.session import close_engine

    await close_engine()


async def reset_db(engine: AsyncEngine | None = None) -> None:
    """Drop all tables and recreate (for testing)."""
    if engine is None:
        engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.warning("Database reset completed")


if __name__ == "__main__":
    # Allow running this module directly for initialization
    asyncio.run(init_db_from_config())
    logger.info("Database initialized successfully")
