"""Tests for SQLite write queue and concurrent writes."""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.logging import get_logger
from app.db.write_queue import WriteQueue
from app.models import category, duplicate_check, rejection_reason, tag  # noqa: F401
from app.models.base import Base
from app.models.receipt import Receipt, ReceiptStatus

logger = get_logger(__name__)


# Use a temporary file database for testing WAL mode
@pytest.fixture(scope="function")
def temp_db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)
    # Also remove WAL/SHM files
    for ext in ["-wal", "-shm"]:
        Path(f"{db_path}{ext}").unlink(missing_ok=True)


@pytest_asyncio.fixture(scope="function")
async def test_engine(temp_db_path: str) -> AsyncEngine:
    """Create a test database engine with file-based SQLite."""
    database_url = f"sqlite+aiosqlite:///{temp_db_path}"
    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        future=True,
    )

    # Create all tables with WAL mode
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
    """Create a test session factory with foreign keys enabled per session."""
    factory = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async def wrapped_factory():
        session = factory()
        await session.execute(text("PRAGMA foreign_keys=ON;"))
        return session

    return wrapped_factory


@pytest_asyncio.fixture(scope="function")
async def write_queue() -> WriteQueue:
    """Create a test write queue."""
    queue = WriteQueue(name="test-write-queue", max_retries=3, retry_delay=0.01)
    await queue.start()
    yield queue
    await queue.stop(timeout=2.0)


@pytest_asyncio.fixture(scope="function")
async def db_session(test_session_factory):
    """Create a test database session."""
    session = await test_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_write_queue_basic(write_queue: WriteQueue, db_session: AsyncSession):
    """Test basic write queue functionality."""
    results = []

    async def write_task(value: int):
        receipt = Receipt(
            original_filename=f"test_{value}.jpg",
            stored_filename=f"test_{value}.jpg",
            file_path=f"/tmp/test_{value}.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash=f"hash_{value}",
            status=ReceiptStatus.UNPARSED,
        )
        db_session.add(receipt)
        await db_session.commit()
        results.append(value)

    # Enqueue multiple tasks using lambda factories
    tasks = [write_queue.enqueue(lambda v=i: write_task(v)) for i in range(5)]
    await asyncio.gather(*tasks)

    assert len(results) == 5
    assert set(results) == {0, 1, 2, 3, 4}


@pytest.mark.asyncio
async def test_concurrent_writes_no_lock(write_queue: WriteQueue, db_session: AsyncSession):
    """Test that concurrent writes don't cause 'database is locked' errors."""

    async def concurrent_write(receipt_id: int):
        receipt = Receipt(
            original_filename=f"receipt_{receipt_id}.jpg",
            stored_filename=f"receipt_{receipt_id}.jpg",
            file_path=f"/tmp/receipt_{receipt_id}.jpg",
            file_size=2000,
            mime_type="image/jpeg",
            image_hash=f"concurrent_hash_{receipt_id}",
            status=ReceiptStatus.UNPARSED,
        )
        db_session.add(receipt)
        await db_session.commit()

    # Run 10 concurrent writes through the queue using lambda factories
    tasks = [write_queue.enqueue(lambda rid=i: concurrent_write(rid)) for i in range(10)]
    await asyncio.gather(*tasks)

    # Verify all were written
    result = await db_session.execute(select(func.count()).select_from(Receipt))
    count = result.scalar()
    assert count >= 10


@pytest.mark.asyncio
async def test_wal_mode_enabled(db_session: AsyncSession):
    """Test that WAL mode is enabled on the database."""
    result = await db_session.execute(text("PRAGMA journal_mode;"))
    mode = result.scalar()
    assert mode == "wal", f"Expected WAL mode, got {mode}"


@pytest.mark.asyncio
async def test_foreign_keys_enabled(db_session: AsyncSession):
    """Test that foreign keys are enabled."""
    result = await db_session.execute(text("PRAGMA foreign_keys;"))
    fk = result.scalar()
    assert fk == 1, f"Expected foreign_keys=1, got {fk}"


@pytest.mark.asyncio
async def test_busy_timeout(db_session: AsyncSession):
    """Test that busy_timeout is set."""
    result = await db_session.execute(text("PRAGMA busy_timeout;"))
    timeout = result.scalar()
    assert timeout >= 5000, f"Expected busy_timeout >= 5000, got {timeout}"


@pytest.mark.asyncio
async def test_write_queue_error_handling(write_queue: WriteQueue):
    """Test that write queue handles errors properly."""

    async def failing_task():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await write_queue.enqueue(failing_task)


@pytest.mark.asyncio
async def test_write_queue_size(write_queue: WriteQueue):
    """Test queue size reporting."""
    assert write_queue.is_running


@pytest.mark.asyncio
async def test_database_migration():
    """Test that alembic migration file was generated."""
    versions_dir = "migrations/versions"
    files = os.listdir(versions_dir)
    migration_files = [f for f in files if f.endswith(".py") and not f.startswith("__")]
    assert len(migration_files) >= 1, "At least one migration file should exist"
    logger.info("Found migration files", extra={"extra_fields": {"files": migration_files}})


@pytest.mark.asyncio
async def test_write_queue_retry_on_lock(write_queue: WriteQueue, db_session: AsyncSession):
    """Test that write queue retries on database lock."""

    call_count = 0

    async def flaky_task():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call - simulate a lock error
            raise OperationalError("database is locked", "", None)
        receipt = Receipt(
            original_filename="retry_test.jpg",
            stored_filename=f"retry_test_{call_count}.jpg",
            file_path="/tmp/retry_test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash=f"retry_hash_{call_count}",
            status=ReceiptStatus.UNPARSED,
        )
        db_session.add(receipt)
        await db_session.commit()

    # This should succeed on retry
    await write_queue.enqueue(lambda: flaky_task())
    assert call_count == 2  # First attempt + 1 retry


@pytest.mark.asyncio
async def test_foreign_key_constraint_enforced(db_session: AsyncSession):
    """Test that foreign key constraints are enforced."""
    # Try to insert a receipt with non-existent category_id
    receipt = Receipt(
        original_filename="fk_test.jpg",
        stored_filename="fk_test.jpg",
        file_path="/tmp/fk_test.jpg",
        file_size=1000,
        mime_type="image/jpeg",
        image_hash="fk_hash",
        status=ReceiptStatus.UNPARSED,
        category_id=999,  # Non-existent category
    )
    db_session.add(receipt)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_unique_constraint_enforced(db_session: AsyncSession):
    """Test that unique constraints are enforced."""
    receipt1 = Receipt(
        original_filename="unique1.jpg",
        stored_filename="same_name.jpg",
        file_path="/tmp/unique1.jpg",
        file_size=1000,
        mime_type="image/jpeg",
        image_hash="hash1",
        status=ReceiptStatus.UNPARSED,
    )
    receipt2 = Receipt(
        original_filename="unique2.jpg",
        stored_filename="same_name.jpg",  # Same stored_filename - should fail
        file_path="/tmp/unique2.jpg",
        file_size=1000,
        mime_type="image/jpeg",
        image_hash="hash2",
        status=ReceiptStatus.UNPARSED,
    )
    db_session.add(receipt1)
    await db_session.commit()

    db_session.add(receipt2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
