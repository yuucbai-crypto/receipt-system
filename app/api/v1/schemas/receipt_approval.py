"""Schemas for Receipt Approval API (approve/reject endpoints)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ReceiptStatus
from app.models.rejection_reason import RejectionReason


class ReceiptApprovalRequest(BaseModel):
    """Request to approve a receipt."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="レシートID")
    approve: bool = Field(..., description="承認の場合True、却下の場合False")


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
    status: ReceiptStatus
    status_message: Optional[str]
    rejection_reason_id: Optional[int] = None
    updated_at: datetime


class RejectionReasonResponse(BaseModel):
    """Response for rejection reason details."""

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

    items: list[RejectionReasonResponse]
    total: int
    page: int
    page_size: int
    total_pages: int