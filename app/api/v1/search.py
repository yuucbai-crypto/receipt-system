"""API endpoints for search operations.

Implements RULE-BE-017: Search index management.
Implements RULE-FLOW-001-14: Search index update for confirmed receipts.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_db_session_dep
from app.schemas.search import (
    RebuildIndexRequest,
    RebuildIndexResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchIndexStatsResponse,
)
from app.core.logging import get_logger
from app.services.search_index_service import get_search_index_service, SearchIndexService

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "/",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート全文検索",
    description="承認済みレシートを全文検索します（店舗名・OCRテキスト・AIコメント・タグ・カテゴリ対象）。",
)
async def search_receipts(
    request: SearchRequest,
    session = Depends(get_db_session_dep),
    search_service: SearchIndexService = Depends(get_search_index_service),
) -> SearchResponse:
    """Full-text search for receipts.

    Searches: store_name, ocr_text, ai_comment, tags, category_name.

    Args:
        request: Search parameters.
        session: Database session.
        search_service: Search index service.

    Returns:
        SearchResponse with matching receipts.
    """
    # Execute search
    results = await search_service.search(
        query=request.query,
        limit=request.limit,
        offset=request.offset,
        category=request.category,
        date_from=request.date_from,
        date_to=request.date_to,
        amount_min=request.amount_min,
        amount_max=request.amount_max,
    )

    # Convert to response items
    items = [
        SearchResultItem(
            receipt_id=r.receipt_id,
            score=r.score,
            store_name=r.store_name,
            total_amount=r.total_amount,
            receipt_date=r.receipt_date,
            category=r.category,
            tags=r.tags,
            snippet=r.snippet,
        )
        for r in results
    ]

    return SearchResponse(
        results=items,
        total=len(items),  # Note: This is current page count, not total matches
        query=request.query,
        limit=request.limit,
        offset=request.offset,
    )


@router.get(
    "/stats",
    response_model=SearchIndexStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="検索インデックス統計取得",
    description="検索インデックスの統計情報を取得します。",
)
async def get_search_index_stats(
    session = Depends(get_db_session_dep),
    search_service: SearchIndexService = Depends(get_search_index_service),
) -> SearchIndexStatsResponse:
    """Get search index statistics.

    Args:
        session: Database session.
        search_service: Search index service.

    Returns:
        SearchIndexStatsResponse.
    """
    stats = await search_service.get_stats()

    return SearchIndexStatsResponse(
        total_documents=stats.total_documents,
        last_updated=stats.last_updated,
        index_size_bytes=stats.index_size_bytes,
    )


@router.post(
    "/rebuild",
    response_model=RebuildIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="検索インデックス再構築",
    description="全レシートから検索インデックスを再構築します。",
)
async def rebuild_search_index(
    request: RebuildIndexRequest,
    session = Depends(get_db_session_dep),
    search_service: SearchIndexService = Depends(get_search_index_service),
) -> RebuildIndexResponse:
    """Rebuild search index from all receipts.

    Args:
        request: Rebuild request (must confirm).
        session: Database session.
        search_service: Search index service.

    Returns:
        RebuildIndexResponse with result.

    Raises:
        HTTPException: If confirm flag is False.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must set confirm=true to rebuild index",
        )

    logger.info("Starting search index rebuild")

    try:
        indexed_count = await search_service.rebuild_index()

        return RebuildIndexResponse(
            success=True,
            indexed_count=indexed_count,
            failed_count=0,
            message=f"Successfully rebuilt index with {indexed_count} documents",
        )
    except Exception as e:
        logger.exception("Search index rebuild failed", extra={"error": str(e)})

        return RebuildIndexResponse(
            success=False,
            indexed_count=0,
            failed_count=0,
            message=f"Index rebuild failed: {e}",
        )


@router.post(
    "/index/{receipt_id}",
    response_model=RebuildIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="単一レシートのインデックス更新",
    description="指定されたレシートの検索インデックスを更新/登録します。",
)
async def index_single_receipt(
    receipt_id: int,
    session = Depends(get_db_session_dep),
    search_service: SearchIndexService = Depends(get_search_index_service),
) -> RebuildIndexResponse:
    """Index or update a single receipt in search index.

    Args:
        receipt_id: Receipt ID to index.
        session: Database session.
        search_service: Search index service.

    Returns:
        RebuildIndexResponse with result.

    Raises:
        HTTPException: If receipt not found.
    """
    from app.models.receipt import Receipt

    receipt = await session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    success = await search_service.index_receipt(receipt)

    if success:
        return RebuildIndexResponse(
            success=True,
            indexed_count=1,
            failed_count=0,
            message=f"Receipt {receipt_id} indexed successfully",
        )
    else:
        return RebuildIndexResponse(
            success=False,
            indexed_count=0,
            failed_count=0,
            message=f"Failed to index receipt {receipt_id}",
        )


@router.delete(
    "/index/{receipt_id}",
    response_model=RebuildIndexResponse,
    status_code=status.HTTP_200_OK,
    summary="単一レシートのインデックス削除",
    description="指定されたレシートを検索インデックスから削除します。",
)
async def remove_from_search_index(
    receipt_id: int,
    session = Depends(get_db_session_dep),
    search_service: SearchIndexService = Depends(get_search_index_service),
) -> RebuildIndexResponse:
    """Remove a receipt from search index.

    Args:
        receipt_id: Receipt ID to remove.
        session: Database session.
        search_service: Search index service.

    Returns:
        RebuildIndexResponse with result.
    """
    success = await search_service.remove_from_index(receipt_id)

    if success:
        return RebuildIndexResponse(
            success=True,
            indexed_count=0,
            failed_count=0,
            message=f"Receipt {receipt_id} removed from index",
        )
    else:
        return RebuildIndexResponse(
            success=False,
            indexed_count=0,
            failed_count=0,
            message=f"Failed to remove receipt {receipt_id} from index",
        )