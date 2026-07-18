"""API schemas for duplicate check endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DuplicateScoreComponentsSchema(BaseModel):
    """Individual score components for duplicate detection."""

    model_config = ConfigDict(from_attributes=True)

    store_name_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    amount_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    image_hash_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    ocr_similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    composite_score: float = Field(..., ge=0.0, le=1.0)
    has_sufficient_data: bool


class DuplicateCheckRequest(BaseModel):
    """Request to check duplicate between two receipts."""

    model_config = ConfigDict(from_attributes=True)

    source_receipt_id: int = Field(..., description="New receipt ID to check")
    target_receipt_id: int = Field(..., description="Existing receipt ID to compare against")
    save_result: bool = Field(True, description="Whether to save result to database")


class DuplicateCheckResponse(BaseModel):
    """Response for duplicate check operation."""

    model_config = ConfigDict(from_attributes=True)

    is_duplicate: bool = Field(..., description="Whether duplicate was detected")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Composite similarity score")
    score_components: DuplicateScoreComponentsSchema = Field(..., description="Individual score components")
    duplicate_check_id: Optional[int] = Field(None, description="ID of saved DuplicateCheck record")
    error: Optional[str] = Field(None, description="Error message if check failed")


class DuplicateCheckListResponse(BaseModel):
    """Response for listing duplicate check records."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_receipt_id: int
    target_receipt_id: int
    composite_score: Optional[float]
    duplicate_threshold: float
    is_duplicate: Optional[bool]
    status: str
    user_confirmed: Optional[bool]
    user_reviewed_at: Optional[datetime]
    user_note: Optional[str]
    created_at: datetime
    updated_at: datetime


class FindDuplicatesRequest(BaseModel):
    """Request to find potential duplicates for a receipt."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="Receipt ID to check for duplicates")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum composite score")


class FindDuplicatesResponse(BaseModel):
    """Response for find duplicates operation."""

    model_config = ConfigDict(from_attributes=True)

    source_receipt_id: int
    potential_duplicates: list[DuplicateCheckResponse]


class DuplicateCheckReviewRequest(BaseModel):
    """Request to review a duplicate check result."""

    model_config = ConfigDict(from_attributes=True)

    user_confirmed: bool = Field(..., description="True if user confirms duplicate, False if not duplicate")
    user_note: Optional[str] = Field(None, max_length=1000, description="Optional user note")


class DuplicateCheckReviewResponse(BaseModel):
    """Response for duplicate check review."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    duplicate_check_id: int
    user_confirmed: bool
    message: str
    error: Optional[str] = None