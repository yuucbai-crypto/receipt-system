"""Schemas package initialization."""

from app.schemas.common import (
    BaseSchema,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    TimestampSchema,
)

from app.schemas.duplicate_check import (
    DuplicateCheckListResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    DuplicateScoreComponentsSchema,
    FindDuplicatesRequest,
    FindDuplicatesResponse,
)

from app.schemas.file_management import (
    ApprovedFileInfo,
    ApprovedFileListRequest,
    ApprovedFileListResponse,
    FileSortRequest,
    FileSortResponse,
)

from app.schemas.receipt_approval import (
    DuplicateReviewRequest,
    DuplicateReviewResponse,
    ReceiptApprovalRequest,
    ReceiptApprovalResponse,
    RejectionReasonCreate,
    RejectionReasonResponse,
)

from app.schemas.search import (
    ReindexRequest,
    ReindexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchIndexStatsResponse,
)

__all__ = [
    # Common
    "BaseSchema",
    "TimestampSchema",
    "ErrorResponse",
    "SuccessResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthResponse",
    # Duplicate check
    "DuplicateScoreComponentsSchema",
    "DuplicateCheckRequest",
    "DuplicateCheckResponse",
    "DuplicateCheckListResponse",
    "FindDuplicatesRequest",
    "FindDuplicatesResponse",
    # Receipt approval
    "RejectionReasonCreate",
    "RejectionReasonResponse",
    "ReceiptApprovalRequest",
    "ReceiptApprovalResponse",
    "DuplicateReviewRequest",
    "DuplicateReviewResponse",
    # File management
    "FileSortRequest",
    "FileSortResponse",
    "ApprovedFileListRequest",
    "ApprovedFileListResponse",
    "ApprovedFileInfo",
    # Search
    "SearchRequest",
    "SearchResponse",
    "SearchResultItem",
    "SearchIndexStatsResponse",
    "ReindexRequest",
    "ReindexResponse",
]