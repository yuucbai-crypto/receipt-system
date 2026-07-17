"""Database initialization and schema creation."""

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings
from app.core.logging import get_logger
from app.db.session import create_engine
from app.models.base import Base

logger = get_logger(__name__)


async def init_db(engine: AsyncEngine) -> None:
    """Initialize database: enable WAL mode, create tables.

    Args:
        engine: Async engine instance
    """
    # Enable WAL mode for SQLite (better concurrency)
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA busy_timeout=5000;"))
        await conn.execute(text("PRAGMA foreign_keys=ON;"))
        await conn.execute(text("PRAGMA cache_size=-32768;"))  # 32MB cache
        await conn.execute(text("PRAGMA temp_store=MEMORY;"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info(
        "Database initialized",
        extra={"extra_fields": {"database_url": str(engine.url)}},
    )


async def init_db_from_settings(settings: Settings) -> None:
    """Initialize database using settings configuration.

    Args:
        settings: Application settings
    """
    # Ensure data directory exists for SQLite file
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings)
    await init_db(engine)


async def close_db(engine: AsyncEngine | None = None) -> None:
    """Close database connections.

    Args:
        engine: Async engine to close (optional)
    """
    from app.db.session import close_engine

    if engine is not None:
        await close_engine(engine)


async def reset_db(engine: AsyncEngine) -> None:
    """Drop all tables and recreate (for testing).

    Args:
        engine: Async engine instance
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.warning("Database reset completed")


if __name__ == "__main__":
    # Allow running this module directly for initialization
    from app.core.config import settings

    asyncio.run(init_db_from_settings(settings))
    logger.info("Database initialized successfully")
