"""Pydantic schemas for settings API."""

from typing import Optional, List
from pydantic import BaseModel


class SettingsResponse(BaseModel):
    """Settings response schema."""

    id: int
    key: str
    value: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class SettingsUpdateRequest(BaseModel):
    """Settings update request schema."""

    value: str
    description: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class SettingsUpdateMultipleRequest(BaseModel):
    """Settings multiple update request schema."""

    settings: List[SettingsUpdateRequest]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class SettingsListResponse(BaseModel):
    """Settings list response schema."""

    items: List[SettingsResponse]
    total: int
    page: int
    page_size: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True