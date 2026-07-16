"""Pytest configuration and fixtures for tests."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.models import category, duplicate_check, receipt, rejection_reason, tag  # noqa: F401
from app.models.base import Base

# Test database URL - use in-memory SQLite for isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_settings(monkeypatch) -> Settings:
    """Create test settings with in-memory database."""
    settings = Settings()
    # Override database URL for testing
    monkeypatch.setattr(settings, "database_url", TEST_DATABASE_URL)
    # Disable logging echo for tests
    monkeypatch.setattr(settings, "database_echo", False)
    return settings


@pytest_asyncio.fixture(scope="function")
async def test_engine(test_settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        await conn.execute(text("PRAGMA busy_timeout=5000;"))
        await conn.execute(text("PRAGMA foreign_keys=ON;"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine: AsyncEngine):
    """Create a test session factory."""
    return sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with foreign keys enabled."""
    async with test_session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys=ON;"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def write_queue():
    """Create a test write queue."""
    from app.db.write_queue import WriteQueue

    queue = WriteQueue(name="test-write-queue", max_retries=3, retry_delay=0.01)
    await queue.start()
    yield queue
    await queue.stop(timeout=2.0)


# Override the global write queue for tests
@pytest.fixture(autouse=True)
def reset_write_queue():
    """Reset global write queue before and after each test."""
    import app.db.write_queue as wq

    # Reset before
    wq._write_queue = None
    yield
    # Reset after
    if wq._write_queue is not None:
        asyncio.run(wq._write_queue.stop(timeout=1.0))
        wq._write_queue = None


@pytest.fixture(autouse=True)
def reset_db_session():
    """Reset global database session/engine before each test."""
    import app.db.session as session_module

    # Reset globals
    session_module._engine = None
    session_module._session_factory = None
    yield
    # Cleanup after
    if session_module._engine is not None:
        asyncio.run(session_module._engine.dispose())
        session_module._engine = None
        session_module._session_factory = None
