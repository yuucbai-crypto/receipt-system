"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.init_db import close_db, init_db_from_config

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    setup_logging()
    logger.info(
        "Application starting up",
        extra={"extra_fields": {"app_name": settings.app_name, "app_env": settings.app_env}},
    )

    # Initialize database
    await init_db_from_config()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Application shutting down")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI駆動型確定申告用レシート管理システム - Backend API",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

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
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    @app.get("/", tags=["Root"], summary="ルートエンドポイント")
    async def root() -> JSONResponse:
        """Root endpoint."""
        return JSONResponse(
            status_code=200,
            content={
                "name": settings.app_name,
                "version": "0.1.0",
                "description": "AI駆動型確定申告用レシート管理システム - Backend API",
                "docs_url": "/docs" if settings.debug else None,
            },
        )

    return app


# Create application instance
app = create_app()
