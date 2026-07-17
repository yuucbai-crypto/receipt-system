"""Write queue for sequential SQLite writes (RULE-ERR-004-2, RULE-BE-013).

This module implements a write queue to prevent 'database is locked' errors
when multiple async tasks try to write to SQLite concurrently.
"""

import asyncio
import contextlib
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Generic, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class QueuedTask(Generic[T]):
    """Represents a queued write task."""

    task_id: str
    coro_factory: Callable[[], Awaitable[T]]
    future: asyncio.Future[T]
    created_at: float = field(default_factory=time.time)


class WriteQueue(Generic[T]):
    """Async write queue for sequential database operations.

    SQLite with WAL mode supports concurrent reads but writes are serialized.
    This queue ensures all write operations are executed sequentially to
    prevent 'database is locked' errors.
    """

    def __init__(
        self,
        name: str = "db-write-queue",
        max_retries: int = 3,
        retry_delay: float = 0.1,
        max_queue_size: int = 1000,
    ):
        """Initialize write queue.

        Args:
            name: Queue name for logging
            max_retries: Maximum retries for locked database
            retry_delay: Base delay between retries (exponential backoff)
            max_queue_size: Maximum queue size (prevents memory leaks)
        """
        self._name = name
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._max_queue_size = max_queue_size

        self._queue: asyncio.Queue[QueuedTask[T]] = asyncio.Queue(maxsize=max_queue_size)
        self._worker_task: asyncio.Task[None] | None = None
        self._running = False
        self._closed = False
        self._task_counter = 0

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def is_running(self) -> bool:
        """Check if queue worker is running."""
        return self._running

    @property
    def is_closed(self) -> bool:
        """Check if queue is closed."""
        return self._closed

    async def start(self) -> None:
        """Start the queue worker."""
        if self._running:
            logger.warning(
                "Write queue already running",
                extra={"extra_fields": {"name": self._name}},
            )
            return

        if self._closed:
            raise RuntimeError(f"Write queue '{self._name}' is closed and cannot be restarted")

        self._running = True
        self._worker_task = asyncio.create_task(self._worker(), name=f"{self._name}-worker")
        logger.info("Write queue started", extra={"extra_fields": {"name": self._name}})

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the queue worker.

        Args:
            timeout: Maximum time to wait for pending tasks
        """
        if not self._running:
            return

        self._running = False

        # Wait for queue to drain
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except TimeoutError:
            logger.warning(
                "Write queue stop timeout, pending tasks may be lost",
                extra={
                    "extra_fields": {
                        "name": self._name,
                        "pending": self._queue.qsize(),
                    }
                },
            )

        # Cancel worker
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task

        self._closed = True
        logger.info("Write queue stopped", extra={"extra_fields": {"name": self._name}})

    async def _worker(self) -> None:
        """Background worker that processes queued write operations."""
        while self._running:
            task: QueuedTask[T] | None = None
            try:
                task = await self._queue.get()

                if not self._running:
                    # Queue is shutting down, re-queue and exit
                    await self._queue.put(task)
                    break

                try:
                    result = await self._execute_with_retry(task.coro_factory)
                    if not task.future.done():
                        task.future.set_result(result)
                except Exception as e:
                    if not task.future.done():
                        task.future.set_exception(e)
            except asyncio.CancelledError:
                # Re-queue the task if we got one before cancellation
                if task is not None:
                    await self._queue.put(task)
                break
            except Exception as e:
                logger.error(
                    "Write queue worker error",
                    extra={"extra_fields": {"name": self._name, "error": str(e)}},
                )
                # Ensure future is resolved with error if we have one
                if task is not None and not task.future.done():
                    task.future.set_exception(e)
            finally:
                # Only call task_done() if we actually retrieved an item
                if task is not None:
                    self._queue.task_done()

    async def _execute_with_retry(self, coro_factory: Callable[[], Awaitable[T]]) -> T:
        """Execute coroutine factory with retry logic for database locks.

        Args:
            coro_factory: Callable that returns a new coroutine each call

        Returns:
            Result of coroutine

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                # Create a fresh coroutine each attempt
                coro = coro_factory()
                return await coro
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # Check for database lock errors
                if any(
                    keyword in error_msg
                    for keyword in [
                        "database is locked",
                        "locked",
                        "busy",
                        "sqlite3.operationalerror",
                    ]
                ) and attempt < self._max_retries:
                    delay = self._retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        "Database locked, retrying",
                        extra={
                            "extra_fields": {
                                "name": self._name,
                                "attempt": attempt + 1,
                                "max_retries": self._max_retries,
                                "delay": delay,
                                "error": str(e),
                            }
                        },
                    )
                    await asyncio.sleep(delay)
                    continue

                # Non-lock error or max retries reached
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("All retries exhausted without exception")

    def enqueue(
        self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any
    ) -> asyncio.Future[T]:
        """Enqueue a write operation.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Future that will be resolved with the result

        Raises:
            RuntimeError: If queue is not running
            RuntimeError: If queue is full (backpressure)
        """
        if not self._running:
            raise RuntimeError(f"Write queue '{self._name}' is not running. Call start() first.")

        if self._closed:
            raise RuntimeError(f"Write queue '{self._name}' is closed")

        if self._queue.full():
            raise RuntimeError(f"Write queue '{self._name}' is full (backpressure)")

        # Create future first, then atomically increment counter and enqueue
        future: asyncio.Future[T] = asyncio.Future()
        self._task_counter += 1
        task_id = f"{self._name}-{self._task_counter}-{uuid.uuid4().hex[:8]}"

        # Create a factory that binds arguments and returns a fresh coroutine each call
        def coro_factory() -> Awaitable[T]:
            return func(*args, **kwargs)

        task = QueuedTask(
            task_id=task_id,
            coro_factory=coro_factory,
            future=future,
        )

        self._queue.put_nowait(task)
        return future

    @asynccontextmanager
    async def enqueue_context(self, coro_factory: Callable[[], Awaitable[T]]) -> AsyncGenerator[T, None]:
        """Context manager for enqueueing operations.

        Usage:
            async with queue.enqueue_context(lambda: db_operation()) as result:
                # result is available after operation completes
                pass

        Args:
            coro_factory: Callable that returns a coroutine

        Yields:
            Result of the coroutine
        """
        future = self.enqueue(coro_factory)
        try:
            result = await future
            yield result
        finally:
            pass


class WriteQueueManager(Generic[T]):
    """Manages write queue lifecycle for dependency injection."""

    def __init__(
        self,
        name: str = "db-write-queue",
        max_retries: int = 3,
        retry_delay: float = 0.1,
        max_queue_size: int = 1000,
    ):
        """Initialize write queue manager.

        Args:
            name: Queue name for logging
            max_retries: Maximum retries for locked database
            retry_delay: Base delay between retries
            max_queue_size: Maximum queue size
        """
        self._queue: WriteQueue[T] = WriteQueue(
            name=name,
            max_retries=max_retries,
            retry_delay=retry_delay,
            max_queue_size=max_queue_size,
        )

    @property
    def queue(self) -> WriteQueue[Any]:
        """Get the write queue instance."""
        return self._queue

    async def start(self) -> None:
        """Start the write queue."""
        await self._queue.start()

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the write queue."""
        await self._queue.stop(timeout)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[WriteQueue[Any], None]:
        """Lifespan context manager for FastAPI."""
        await self.start()
        try:
            yield self._queue
        finally:
            await self.stop()


async def create_write_queue_manager(
    name: str = "db-write-queue",
    max_retries: int = 3,
    retry_delay: float = 0.1,
    max_queue_size: int = 1000,
) -> WriteQueueManager[Any]:
    """Factory function to create and start write queue manager.

    Args:
        name: Queue name for logging
        max_retries: Maximum retries for locked database
        retry_delay: Base delay between retries
        max_queue_size: Maximum queue size

    Returns:
        Started WriteQueueManager
    """
    manager: WriteQueueManager[Any] = WriteQueueManager[
        Any
    ](
        name=name,
        max_retries=max_retries,
        retry_delay=retry_delay,
        max_queue_size=max_queue_size,
    )
    await manager.start()
    return manager
