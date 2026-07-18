"""FastAPI dependencies for API endpoints."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session as _get_session
from app.state import get_app_state


async def get_db_session_dep():
    """Get database session dependency for API endpoints.

    Creates a new session for each request.

    Yields:
        AsyncSession: Database session.
    """
    session_factory = get_app_state().session_factory
    if session_factory is None:
        raise RuntimeError("Database session factory not initialized")
    async with _get_session(session_factory) as session:
        yield session