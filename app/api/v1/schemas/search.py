"""Schemas for Search API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Search request parameters."""

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., min_length=1, max_length=500, description="検索クエリ")
    limit: int = Field(default=20, ge=1, le=100, description="最大件数")
    offset: int = Field(default=0, ge=0, description="オフセット")
    category: Optional[str] = Field(None, description="カテゴリでフィルタ")
    date_from: Optional[datetime] = Field(None, description="日付範囲開始")
    date_to: Optional[datetime] = Field(None, description="日付範囲終了")
    amount_min: Optional[int] = Field(None, ge=0, description="最小金額")
    amount_max: Optional[int] = Field(None, ge=0, description="最大金額")


class SearchResultItem(BaseModel):
    """Single search result item."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int
    score: float
    store_name: Optional[str]
    total_amount: Optional[int]
    receipt_date: Optional[datetime]
    category: Optional[str]
    tags: list[str]
    snippet: str


class SearchResponse(BaseModel):
    """Search response."""

    model_config = ConfigDict(from_attributes=True)

    results: list[SearchResultItem]
    total: int
    query: str
    limit: int
    offset: int


class SearchIndexStatsResponse(BaseModel):
    """Search index statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_documents: int
    last_updated: Optional[datetime]
    index_size_bytes: int


class RebuildIndexRequest(BaseModel):
    """Request to rebuild search index."""

    model_config = ConfigDict(from_attributes=True)

    confirm: bool = Field(default=False, description="確認フラグ（Trueで実行）")


class RebuildIndexResponse(BaseModel):
    """Response for index rebuild."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    indexed_count: int
    message: str