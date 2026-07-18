"""Schemas for File Management API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.services.file_sorting_service import FileSortResult


class FileSortRequest(BaseModel):
    """Request to sort an approved receipt file."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="レシートID")


class FileSortResponse(BaseModel):
    """Response for file sort operation."""

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

    category: Optional[str] = Field(None, description="カテゴリフォルダ名でフィルタ")
    year_month: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$", description="年月フォルダでフィルタ (YYYY-MM)")
    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=20, ge=1, le=100, description="ページサイズ")


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
    """Paginated list of approved files."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ApprovedFileInfo]
    total: int
    page: int
    page_size: int
    total_pages: int