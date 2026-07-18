"""Duplicate Check API Schemas.

Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.duplicate_check import DuplicateCheckStatus
from app.services.duplicate_check_service import DuplicateScoreComponents


class DuplicateScoreComponentsSchema(BaseModel):
    """Individual score components for duplicate detection."""

    model_config = ConfigDict(from_attributes=True)

    store_name_score: Optional[float] = Field(None, description="店舗名類似度 (0.0-1.0)")
    amount_score: Optional[float] = Field(None, description="金額類似度 (0.0-1.0)")
    date_score: Optional[float] = Field(None, description="日付類似度 (0.0-1.0)")
    metadata_score: Optional[float] = Field(None, description="メタデータ類似度 (0.0-1.0)")
    image_hash_score: Optional[float] = Field(None, description="画像ハッシュ類似度 (0.0-1.0)")
    ocr_similarity_score: Optional[float] = Field(None, description="OCRテキスト類似度 (0.0-1.0)")
    composite_score: float = Field(..., description="総合スコア (0.0-1.0)")
    has_sufficient_data: bool = Field(..., description="比較に十分なデータがあるか")


class DuplicateCheckRequest(BaseModel):
    """Request to check duplicate between two receipts."""

    model_config = ConfigDict(from_attributes=True)

    source_receipt_id: int = Field(..., description="比較元レシートID（新規）")
    target_receipt_id: int = Field(..., description="比較対象レシートID（既存）")
    save_result: bool = Field(True, description="結果をDBに保存するか")


class DuplicateCheckResponse(BaseModel):
    """Response for duplicate check."""

    model_config = ConfigDict(from_attributes=True)

    is_duplicate: bool = Field(..., description="重複判定結果")
    composite_score: float = Field(..., description="総合類似度スコア (0.0-1.0)")
    score_components: DuplicateScoreComponentsSchema = Field(..., description="個別スコア構成要素")
    duplicate_check_id: Optional[int] = Field(None, description="保存されたDuplicateCheckレコードID")
    error: Optional[str] = Field(None, description="エラーメッセージ（失敗時）")


class FindDuplicatesRequest(BaseModel):
    """Request to find potential duplicates for a receipt."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int = Field(..., description="検索対象レシートID")
    limit: int = Field(10, ge=1, le=50, description="最大取得件数")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="最小スコア閾値")


class FindDuplicatesResponse(BaseModel):
    """Response for find duplicates."""

    model_config = ConfigDict(from_attributes=True)

    source_receipt_id: int = Field(..., description="検索対象レシートID")
    potential_duplicates: list[DuplicateCheckResponse] = Field(..., description="重複候補一覧（スコア降順）")


class DuplicateCheckListResponse(BaseModel):
    """Duplicate check record for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_receipt_id: int
    target_receipt_id: int
    store_name_score: Optional[float]
    amount_score: Optional[float]
    date_score: Optional[float]
    metadata_score: Optional[float]
    image_hash_score: Optional[float]
    ocr_similarity_score: Optional[float]
    composite_score: Optional[float]
    duplicate_threshold: float
    is_duplicate: Optional[bool]
    status: DuplicateCheckStatus
    user_confirmed: Optional[bool]
    user_reviewed_at: Optional[datetime]
    user_note: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class DuplicateCheckReviewRequest(BaseModel):
    """Request to review a duplicate check result."""

    model_config = ConfigDict(from_attributes=True)

    user_confirmed: bool = Field(..., description="ユーザーが重複と判定した場合True")
    user_note: Optional[str] = Field(None, max_length=1000, description="ユーザーメモ")


class DuplicateCheckReviewResponse(BaseModel):
    """Response for duplicate check review."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_receipt_id: int
    target_receipt_id: int
    is_duplicate: Optional[bool]
    user_confirmed: Optional[bool]
    user_reviewed_at: Optional[datetime]
    user_note: Optional[str]
    status: DuplicateCheckStatus
    updated_at: datetime