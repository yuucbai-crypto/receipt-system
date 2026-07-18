"""Application state container for dependency injection."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings


class AppState:
    """Application state container for dependency injection."""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.settings: Settings | None = None


_app_state = AppState()


def get_app_state() -> AppState:
    """Get application state singleton."""
    return _app_state