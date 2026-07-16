"""Common Pydantic schemas."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class ErrorResponse(BaseSchema):
    """Standard error response schema."""

    error: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    details: dict[str, Any] | None = Field(None, description="詳細情報")


class SuccessResponse(BaseSchema, Generic[T]):
    """Standard success response schema."""

    success: bool = Field(default=True, description="成功フラグ")
    message: str = Field(..., description="メッセージ")
    data: T | None = Field(None, description="データ")


class PaginationParams(BaseSchema):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=20, ge=1, le=100, description="ページサイズ")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response schema."""

    items: list[T] = Field(..., description="アイテム一覧")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在のページ")
    page_size: int = Field(..., description="ページサイズ")
    total_pages: int = Field(..., description="総ページ数")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class HealthResponse(BaseSchema):
    """Health check response schema."""

    status: str = Field(..., description="ステータス")
    version: str = Field(default="1.0.0", description="バージョン")
    timestamp: datetime = Field(default_factory=datetime.now, description="タイムスタンプ")
