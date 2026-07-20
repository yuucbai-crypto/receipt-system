"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.api.v1 import duplicate_check, file_management, receipt_approval, receipts, search
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.db.init_db import close_db, init_db_from_settings
from app.db.session import close_engine, create_engine, create_session_factory
from app.state import get_app_state

logger = get_logger(__name__)


async def get_settings_dep() -> Settings | None:
    """FastAPI dependency for settings."""
    return get_app_state().settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure FastAPI application (Factory pattern).

    Args:
        settings: Application settings (optional, uses get_settings() if not provided)

    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan handler."""
        # Startup
        state = get_app_state()
        state.settings = settings
        setup_logging()
        logger.info(
            "Application starting up",
            extra={
                "extra_fields": {
                    "app_name": settings.app_name,
                    "app_env": settings.app_env,
                }
            },
        )

        # Initialize database
        state.engine = create_engine(settings)
        state.session_factory = create_session_factory(state.engine)
        await init_db_from_settings(settings)
        logger.info("Database initialized")

        yield

        # Shutdown
        logger.info("Application shutting down")
        await close_engine(state.engine)
        await close_db(state.engine)
        state.engine = None
        state.session_factory = None
        logger.info("Database connections closed")

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI駆動型確定申告用レシート管理システム - Backend API",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Include API routers
    app.include_router(duplicate_check.router, prefix="/api/v1")
    app.include_router(receipt_approval.router, prefix="/api/v1")
    app.include_router(file_management.router, prefix="/api/v1")
    app.include_router(receipts.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")

    @app.get("/health", tags=["Health"], summary="ヘルスチェック")
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSONResponse: Health status with version and timestamp
        """
        from datetime import datetime

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )

    @app.get("/", tags=["Root"], summary="ルートエンドポイント")
    async def root() -> JSONResponse:
        """Root endpoint - minimal response."""
        return JSONResponse(
            status_code=200,
            content={"status": "ok"},
        )

    return app


# Create application instance with default settings
app = create_app()


def get_session_factory_dep() -> async_sessionmaker[AsyncSession] | None:
    """FastAPI dependency for session factory."""
    return get_app_state().session_factory