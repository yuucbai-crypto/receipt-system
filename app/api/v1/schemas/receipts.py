"""Schemas for Receipts API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReceiptListRequest(BaseModel):
    """Request parameters for listing receipts."""

    model_config = ConfigDict(from_attributes=True)

    status: Optional[str] = Field(None, description="Filter by status")
    category_id: Optional[int] = Field(None, description="Filter by category ID")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")


class ReceiptResponse(BaseModel):
    """Receipt response item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str
    image_hash: str
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_language: str
    receipt_date: Optional[datetime] = None
    store_name: Optional[str] = None
    total_amount: Optional[int] = None
    tax_amount: Optional[int] = None
    currency: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_confidence: Optional[float] = None
    ai_comment: Optional[str] = None
    ai_model: Optional[str] = None
    ai_confidence: Optional[float] = None
    status: str
    status_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    retry_count: int
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReceiptListResponse(BaseModel):
    """Paginated receipt list response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ReceiptResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[ReceiptResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "ReceiptListResponse":
        """Create paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ReceiptDetailResponse(ReceiptResponse):
    """Detailed receipt response (extends list response with more details)."""

    pass


class ReceiptImageResponse(BaseModel):
    """Receipt image response."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int
    image_url: str
    mime_type: str
    file_size: int