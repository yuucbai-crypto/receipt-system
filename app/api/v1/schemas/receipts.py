"""Pydantic schemas for receipts API."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ReceiptResponse(BaseModel):
    """Receipt response schema."""

    id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str
    image_hash: str
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_language: Optional[str] = None
    receipt_date: datetime
    store_name: str
    total_amount: float
    tax_amount: Optional[float] = None
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
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptDetailResponse(BaseModel):
    """Receipt detail response schema."""

    id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str
    image_hash: str
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_language: Optional[str] = None
    receipt_date: datetime
    store_name: str
    total_amount: float
    tax_amount: Optional[float] = None
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
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptImageResponse(BaseModel):
    """Receipt image response schema."""

    receipt_id: int
    image_url: str
    mime_type: str
    file_size: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptListRequest(BaseModel):
    """Receipt list request schema."""

    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    category_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptListResponse(BaseModel):
    """Receipt list response schema."""

    items: List[ReceiptResponse]
    total: int
    page: int
    page_size: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptReprocessRequest(BaseModel):
    """Receipt reprocess request schema."""

    force: bool = False

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptDeleteResponse(BaseModel):
    """Receipt delete response schema."""

    success: bool
    message: str

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ReceiptReprocessResponse(BaseModel):
    """Receipt reprocess response schema."""

    success: bool
    message: str
    receipt_id: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True