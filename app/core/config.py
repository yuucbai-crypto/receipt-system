"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",  # No prefix for flexibility
    )

    # Application
    app_name: str = Field(default="receipt-system", description="Application name")
    app_env: str = Field(
        default="development", description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Debug mode (from env)")
    host: str = Field(default="0.0.0.0", description="Host to bind")
    port: int = Field(default=8000, description="Port to bind")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/receipts.db",
        description="Database connection URL (SQLite with aiosqlite for async)",
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    @field_validator("database_url", mode="before")
    @classmethod
    def _validate_database_url(cls, v: str | Path) -> str:
        """Ensure database_url is a string, not Path."""
        return str(v) if isinstance(v, Path) else v

    # OpenRouter API
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key for AI analysis",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="OpenRouter model to use for analysis",
    )
    openrouter_timeout: int = Field(default=60, description="OpenRouter API timeout in seconds")
    openrouter_max_retries: int = Field(default=3, description="Max retries for OpenRouter API")

    # File system directories (required by RULE-GEN-019)
    unparsed_dir: Path = Field(
        default=Path("./data/unparsed"),
        description="Directory for unparsed receipt images",
    )
    unapproved_dir: Path = Field(
        default=Path("./data/unapproved"),
        description="Directory for unapproved receipt images",
    )
    failed_dir: Path = Field(
        default=Path("./data/failed"),
        description="Directory for failed receipt images",
    )
    approved_dir: Path = Field(
        default=Path("./data/approved"),
        description="Directory for approved receipt images",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    log_format: str = Field(default="json", description="Log format: json or text")

    # File watching
    watchdog_poll_interval: float = Field(
        default=1.0, description="File watcher poll interval in seconds"
    )
    watchdog_recursive: bool = Field(default=False, description="Watch directories recursively")

    # OCR
    ocr_language: str = Field(default="jpn+eng", description="OCR language (Tesseract)")
    ocr_dpi: int = Field(default=300, description="OCR DPI for image preprocessing")

    # Duplicate detection
    duplicate_threshold: float = Field(
        default=0.85, description="Duplicate detection threshold (0.0-1.0)"
    )
    duplicate_image_hash_threshold: float = Field(
        default=0.95, description="Image hash similarity threshold"
    )
    duplicate_ocr_similarity_threshold: float = Field(
        default=0.90, description="OCR text similarity threshold"
    )

    # File processing
    supported_image_extensions: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"],
        description="Supported image file extensions",
    )
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")

    # Pagination defaults
    default_page_size: int = Field(default=20, description="Default page size for pagination")
    max_page_size: int = Field(default=100, description="Maximum page size for pagination")

    def model_post_init(self, __context: Any) -> None:
        """Create directories if they don't exist."""
        for dir_path in [
            self.unparsed_dir,
            self.unapproved_dir,
            self.failed_dir,
            self.approved_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Global settings instance (lazy initialization)
_settings: Settings | None = None
settings = Settings()  # For backward compatibility; use get_settings() for DI
