"""API schemas for search endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Search request parameters."""

    model_config = ConfigDict(from_attributes=True)

    query: str = Field(..., min_length=1, description="Search query (supports FTS5 syntax)")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Pagination offset")
    category: Optional[str] = Field(None, description="Filter by category")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")
    amount_min: Optional[int] = Field(None, ge=0, description="Minimum amount")
    amount_max: Optional[int] = Field(None, ge=0, description="Maximum amount")


class SearchResultItem(BaseModel):
    """Individual search result."""

    model_config = ConfigDict(from_attributes=True)

    receipt_id: int
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    store_name: Optional[str]
    total_amount: Optional[int]
    receipt_date: Optional[datetime]
    category: Optional[str]
    tags: list[str]
    snippet: str


class SearchResponse(BaseModel):
    """Search response."""

    model_config = ConfigDict(from_attributes=True)

    query: str
    results: list[SearchResultItem]
    total: int
    limit: int
    offset: int


class SearchIndexStatsResponse(BaseModel):
    """Search index statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_documents: int
    last_updated: Optional[datetime]
    index_size_bytes: int


class ReindexRequest(BaseModel):
    """Request to rebuild search index."""

    model_config = ConfigDict(from_attributes=True)

    receipt_ids: Optional[list[int]] = Field(None, description="Specific receipt IDs to reindex (None = all)")
    batch_size: int = Field(100, ge=1, le=1000, description="Batch size for reindexing")
    confirm: bool = Field(False, description="Confirm rebuild operation")


class RebuildIndexRequest(ReindexRequest):
    """Alias for ReindexRequest for API compatibility."""
    pass


class ReindexResponse(BaseModel):
    """Response for reindex operation."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    indexed_count: int
    failed_count: int
    message: str
    error: Optional[str] = None


class RebuildIndexResponse(ReindexResponse):
    """Alias for ReindexResponse for API compatibility."""
    pass