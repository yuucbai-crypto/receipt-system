"""Write queue for sequential SQLite writes (RULE-ERR-004-2, RULE-BE-013).

This module implements a write queue to prevent 'database is locked' errors
when multiple async tasks try to write to SQLite concurrently.
"""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, Generic, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


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
    ):
        """Initialize write queue.

        Args:
            name: Queue name for logging
            max_retries: Maximum retries for locked database
            retry_delay: Base delay between retries (exponential backoff)
        """
        self._queue: asyncio.Queue[tuple[int, Callable[[], Awaitable[T]], asyncio.Future[T]]] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._name = name
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._results: dict[int, asyncio.Future[T]] = {}
        self._counter = 0

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def is_running(self) -> bool:
        """Check if queue worker is running."""
        return self._running

    async def start(self) -> None:
        """Start the queue worker."""
        if self._running:
            logger.warning(
                "Write queue already running", extra={"extra_fields": {"name": self._name}}
            )
            return

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
                extra={"extra_fields": {"name": self._name, "pending": self._queue.qsize()}},
            )

        # Cancel worker
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task

        logger.info("Write queue stopped", extra={"extra_fields": {"name": self._name}})

    async def _worker(self) -> None:
        """Background worker that processes queued write operations."""
        while self._running:
            task_id = None
            coro_factory = None
            future = None
            try:
                task_id, coro_factory, future = await self._queue.get()

                if not self._running:
                    # Queue is shutting down, task will not be processed
                    # No need to call task_done() as we didn't process it
                    # Put it back for any remaining workers (though there shouldn't be any)
                    await self._queue.put((task_id, coro_factory, future))
                    break

                try:
                    result = await self._execute_with_retry(coro_factory)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)  # type: ignore[arg-type]
            except asyncio.CancelledError:
                # Re-queue the task if we got one before cancellation
                if task_id is not None and coro_factory is not None and future is not None:
                    await self._queue.put((task_id, coro_factory, future))
                break
            except Exception as e:
                logger.error(
                    "Write queue worker error",
                    extra={"extra_fields": {"name": self._name, "error": str(e)}},
                )
                # Ensure future is resolved with error if we have one
                if future is not None and not future.done():
                    future.set_exception(e)  # type: ignore[arg-type]
            finally:
                # Only call task_done() if we actually retrieved an item
                if task_id is not None:
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
        """
        if not self._running:
            raise RuntimeError(f"Write queue '{self._name}' is not running. Call start() first.")

        # Create future first, then atomically increment counter and enqueue
        future: asyncio.Future[T] = asyncio.Future()
        self._counter += 1
        task_id = self._counter

        # Create a factory that binds arguments and returns a fresh coroutine each call
        def coro_factory() -> Awaitable[T]:
            return func(*args, **kwargs)

        self._queue.put_nowait((task_id, coro_factory, future))
        return future

    @asynccontextmanager
    async def enqueue_context(self, coro_factory: Callable[[], Awaitable[T]]):
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


# Global write queue instance
_write_queue: WriteQueue | None = None


async def get_write_queue() -> WriteQueue:
    """Get or create the global write queue."""
    global _write_queue
    if _write_queue is None:
        _write_queue = WriteQueue()
        await _write_queue.start()
    return _write_queue


async def close_write_queue() -> None:
    """Close the global write queue."""
    global _write_queue
    if _write_queue is not None:
        await _write_queue.stop()
        _write_queue = None


@asynccontextmanager
async def write_transaction():
    """Context manager for executing write operations sequentially.

    Usage:
        async with write_transaction() as queue:
            await queue.enqueue(lambda: session.add(obj))
            await queue.enqueue(lambda: session.commit())

    Yields:
        WriteQueue instance
    """
    queue = await get_write_queue()
    yield queue
