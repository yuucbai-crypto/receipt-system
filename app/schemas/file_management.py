"""API schemas for file management endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FileSortRequest(BaseModel):
    """Request to sort an approved receipt file."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="Approved receipt ID")
    source_path: Optional[str] = Field(None, description="Optional source path override")


class FileSortResponse(BaseModel):
    """Response for file sorting operation."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    receipt_id: int
    source_path: str
    destination_path: Optional[str] = None
    new_filename: Optional[str] = None
    category_folder: Optional[str] = None
    year_month_folder: Optional[str] = None
    error: Optional[str] = None


class ApprovedFileListRequest(BaseModel):
    """Request to list approved files."""

    model_config = ConfigDict(from_attributes=True)

    category: Optional[str] = Field(None, description="Filter by category folder")
    year_month: Optional[str] = Field(None, description="Filter by year-month (YYYY-MM)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")


class ApprovedFileInfo(BaseModel):
    """Approved file information."""

    model_config = ConfigDict(from_attributes=True)

    filename: str
    filepath: str
    category_folder: str
    year_month_folder: str
    file_size: int
    modified_at: datetime


class ApprovedFileListResponse(BaseModel):
    """Response for approved file list."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ApprovedFileInfo]
    total: int
    page: int
    page_size: int
    total_pages: int