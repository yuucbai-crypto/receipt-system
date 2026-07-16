"""Structured logging configuration (JSON format)."""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable text log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()
        module = record.module
        func = record.funcName
        line = record.lineno

        base = f"{timestamp} | {level:8} | {logger_name} | {module}:{func}:{line} | {message}"

        if hasattr(record, "extra_fields") and record.extra_fields:
            extras = " | ".join(f"{k}={v}" for k, v in record.extra_fields.items())
            base += f" | {extras}"

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)

        return base


def setup_logging() -> None:
    """Configure application logging (INFO/WARNING/ERROR levels)."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Choose formatter based on config
    formatter = JsonFormatter() if settings.log_format.lower() == "json" else TextFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "extra_fields": {"log_level": settings.log_level, "log_format": settings.log_format}
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to provide logger property to classes."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
