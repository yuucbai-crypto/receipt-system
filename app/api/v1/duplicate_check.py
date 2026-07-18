"""API endpoints for duplicate check operations.

Implements RULE-BE-006: Duplicate check API endpoints.
Implements RULE-FLOW-001-7: Duplicate candidate check.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.v1.dependencies import get_db_session_dep
from app.schemas.duplicate_check import (
    DuplicateCheckListResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    DuplicateCheckReviewRequest,
    DuplicateCheckReviewResponse,
    DuplicateScoreComponentsSchema,
    FindDuplicatesRequest,
    FindDuplicatesResponse,
)
from app.core.logging import get_logger
from app.models.duplicate_check import DuplicateCheck, DuplicateCheckStatus
from app.models.receipt import Receipt
from app.services.duplicate_check_service import DuplicateCheckService, get_duplicate_check_service

logger = get_logger(__name__)

router = APIRouter(prefix="/duplicate-check", tags=["Duplicate Check"])


@router.post(
    "/check",
    response_model=DuplicateCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="重複チェック実行",
    description="2つのレシート間で重複チェックを実行し、総合スコアを計算します。",
)
async def check_duplicate(
    request: DuplicateCheckRequest,
    session = Depends(get_db_session_dep),
    service: DuplicateCheckService = Depends(get_duplicate_check_service),
) -> DuplicateCheckResponse:
    """Execute duplicate check between two receipts.

    Args:
        request: Duplicate check request with source and target receipt IDs.
        session: Database session.
        service: Duplicate check service.

    Returns:
        DuplicateCheckResponse with scores and duplicate decision.

    Raises:
        HTTPException: If receipts not found.
    """
    # Verify source receipt exists
    source = await session.get(Receipt, request.source_receipt_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source receipt {request.source_receipt_id} not found",
        )

    # Verify target receipt exists
    target = await session.get(Receipt, request.target_receipt_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target receipt {request.target_receipt_id} not found",
        )

    # Prevent self-comparison
    if source.id == target.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare receipt with itself",
        )

    # Execute duplicate check
    result = await service.check_duplicate(
        source_receipt=source,
        target_receipt=target,
        save_result=request.save_result,
    )

    return DuplicateCheckResponse(
        is_duplicate=result.is_duplicate,
        composite_score=result.composite_score,
        score_components=DuplicateScoreComponentsSchema.model_validate(result.score_components),
        duplicate_check_id=result.duplicate_check_id,
        error=result.error,
    )


@router.post(
    "/find",
    response_model=FindDuplicatesResponse,
    status_code=status.HTTP_200_OK,
    summary="重複候補検索",
    description="指定されたレシートの重複候補を検索します。",
)
async def find_duplicates(
    request: FindDuplicatesRequest,
    session = Depends(get_db_session_dep),
    service: DuplicateCheckService = Depends(get_duplicate_check_service),
) -> FindDuplicatesResponse:
    """Find potential duplicates for a receipt.

    Args:
        request: Find duplicates request.
        session: Database session.
        service: Duplicate check service.

    Returns:
        FindDuplicatesResponse with list of potential duplicates.

    Raises:
        HTTPException: If receipt not found.
    """
    # Verify receipt exists
    receipt = await session.get(Receipt, request.receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {request.receipt_id} not found",
        )

    # Find potential duplicates
    results = await service.find_potential_duplicates(
        source_receipt=receipt,
        limit=request.limit,
    )

    # Filter by min_score
    filtered = [r for r in results if r.composite_score >= request.min_score]

    return FindDuplicatesResponse(
        source_receipt_id=receipt.id,
        potential_duplicates=[
            DuplicateCheckResponse(
                is_duplicate=r.is_duplicate,
                composite_score=r.composite_score,
                score_components=DuplicateScoreComponentsSchema.model_validate(r.score_components),
                duplicate_check_id=r.duplicate_check_id,
                error=r.error,
            )
            for r in filtered
        ],
    )


@router.get(
    "/{duplicate_check_id}",
    response_model=DuplicateCheckListResponse,
    status_code=status.HTTP_200_OK,
    summary="重複チェック結果取得",
    description="重複チェック結果の詳細を取得します。",
)
async def get_duplicate_check(
    duplicate_check_id: int,
    session = Depends(get_db_session_dep),
) -> DuplicateCheckListResponse:
    """Get duplicate check result by ID.

    Args:
        duplicate_check_id: DuplicateCheck record ID.
        session: Database session.

    Returns:
        DuplicateCheckListResponse with check details.

    Raises:
        HTTPException: If record not found.
    """
    record = await session.get(DuplicateCheck, duplicate_check_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duplicate check {duplicate_check_id} not found",
        )

    return DuplicateCheckListResponse.model_validate(record)


@router.post(
    "/{duplicate_check_id}/review",
    response_model=DuplicateCheckReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="重複チェック結果レビュー",
    description="ユーザーによる重複判定結果を記録します。",
)
async def review_duplicate_check(
    duplicate_check_id: int,
    request: DuplicateCheckReviewRequest,
    session = Depends(get_db_session_dep),
) -> DuplicateCheckReviewResponse:
    """Record user's duplicate review decision.

    Args:
        duplicate_check_id: DuplicateCheck record ID.
        request: Review decision.
        session: Database session.

    Returns:
        DuplicateCheckReviewResponse with updated record.

    Raises:
        HTTPException: If record not found.
    """
    record = await session.get(DuplicateCheck, duplicate_check_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Duplicate check {duplicate_check_id} not found",
        )

    from datetime import datetime, timezone

    record.user_confirmed = request.user_confirmed
    record.user_reviewed_at = datetime.now(timezone.utc)
    record.user_note = request.user_note
    record.status = DuplicateCheckStatus.USER_REVIEWED

    await session.commit()
    await session.refresh(record)

    logger.info(
        "Duplicate check reviewed",
        extra={
            "duplicate_check_id": duplicate_check_id,
            "user_confirmed": request.user_confirmed,
        },
    )

    return DuplicateCheckReviewResponse.model_validate(record)


@router.get(
    "/receipt/{receipt_id}/checks",
    response_model=list[DuplicateCheckListResponse],
    status_code=status.HTTP_200_OK,
    summary="レシートの重複チェック履歴取得",
    description="指定されたレシートに関連する重複チェック履歴を取得します。",
)
async def get_receipt_duplicate_checks(
    receipt_id: int,
    session = Depends(get_db_session_dep),
) -> list[DuplicateCheckListResponse]:
    """Get duplicate check history for a receipt.

    Args:
        receipt_id: Receipt ID.
        session: Database session.

    Returns:
        List of DuplicateCheckListResponse.
    """
    # Verify receipt exists
    receipt = await session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    # Query checks where this receipt is source or target
    from sqlalchemy import or_

    stmt = select(DuplicateCheck).where(
        or_(
            DuplicateCheck.source_receipt_id == receipt_id,
            DuplicateCheck.target_receipt_id == receipt_id,
        )
    ).order_by(DuplicateCheck.created_at.desc())

    result = await session.execute(stmt)
    records = result.scalars().all()

    return [DuplicateCheckListResponse.model_validate(r) for r in records]