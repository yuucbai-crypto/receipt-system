"""API schemas for receipt approval/rejection endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RejectionReasonCreate(BaseModel):
    """Request to create a rejection reason."""

    model_config = ConfigDict(from_attributes=True)

    reason_code: str = Field(..., min_length=1, max_length=50, description="Reason code (e.g., 'DUPLICATE', 'INVALID_AMOUNT')")
    reason_category: str = Field(..., min_length=1, max_length=50, description="Reason category (e.g., 'DUPLICATE', 'DATA_QUALITY', 'NOT_BUSINESS')")
    reason_text: str = Field(..., min_length=1, description="Detailed reason text")
    user_note: Optional[str] = Field(None, description="Optional user note")
    is_for_ai_training: bool = Field(False, description="Whether this can be used for AI training")


class RejectionReasonResponse(BaseModel):
    """Response for rejection reason."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_id: int
    reason_code: str
    reason_category: str
    reason_text: str
    user_note: Optional[str]
    ai_feedback: Optional[str]
    is_for_ai_training: bool
    created_at: datetime
    updated_at: datetime


class RejectionReasonListResponse(BaseModel):
    """Paginated list of rejection reasons."""

    model_config = ConfigDict(from_attributes=True)

    items: list[RejectionReasonResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReceiptApprovalRequest(BaseModel):
    """Request to approve a receipt."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="Receipt ID to approve/reject")
    approve: bool = Field(..., description="True to approve, False to reject")
    rejection_reason: Optional[RejectionReasonCreate] = Field(None, description="Required if approve=False")
    user_note: Optional[str] = Field(None, description="Optional user note")


class ReceiptRejectRequest(BaseModel):
    """Request to reject a receipt with reason."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="レシートID")
    reason_code: str = Field(..., max_length=50, description="却下理由コード")
    reason_text: str = Field(..., max_length=500, description="却下理由テキスト")
    user_note: Optional[str] = Field(None, max_length=1000, description="ユーザーメモ")
    is_for_ai_training: bool = Field(default=False, description="AI学習用データとして使用")


class ReceiptApprovalResponse(BaseModel):
    """Response for receipt approval/rejection."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int
    status: str
    status_message: Optional[str]
    rejection_reason_id: Optional[int] = None
    updated_at: datetime


class DuplicateReviewRequest(BaseModel):
    """Request to record user's duplicate review decision."""

    model_config = ConfigDict(from_attributes=True)

    duplicate_check_id: int = Field(..., description="DuplicateCheck record ID")
    user_confirmed: bool = Field(..., description="True if user confirms duplicate, False if not duplicate")
    user_note: Optional[str] = Field(None, description="Optional user note")


class DuplicateReviewResponse(BaseModel):
    """Response for duplicate review."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    duplicate_check_id: int
    user_confirmed: bool
    message: str
    error: Optional[str] = None