"""API v1 package initialization."""

from app.api.v1 import (
    dashboard,
    duplicate_check,
    file_management,
    files,
    receipt_approval,
    receipts,
    search,
    settings,
    stats,
)

__all__ = [
    "dashboard",
    "duplicate_check",
    "file_management",
    "files",
    "receipt_approval",
    "receipts",
    "search",
    "settings",
    "stats",
]