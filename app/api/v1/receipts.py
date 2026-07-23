"""API endpoints for receipts.

Implements RULE-BE-005: Receipt list API.
Implements RULE-BE-006: Receipt detail API.
Implements RULE-BE-007: Receipt image API.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import get_db_session_dep
from app.api.v1.schemas.receipts import (
    ReceiptDeleteResponse,
    ReceiptDetailResponse,
    ReceiptImageResponse,
    ReceiptListRequest,
    ReceiptListResponse,
    ReceiptReprocessRequest,
    ReceiptReprocessResponse,
    ReceiptResponse,
)
from app.core.logging import get_logger
from app.models.category import Category
from app.models.receipt import Receipt, ReceiptStatus
from app.models.tag import Tag

logger = get_logger(__name__)

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.get(
    "",
    response_model=ReceiptListResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート一覧取得",
    description="レシートの一覧を取得します（フィルタ・ページング対応）。",
)
async def list_receipts(
    request: Annotated[ReceiptListRequest, Depends()],
    session=Depends(get_db_session_dep),
) -> ReceiptListResponse:
    """List receipts with filtering and pagination.

    Implements RULE-BE-005.

    Args:
        request: List request with filters and pagination.
        session: Database session.

    Returns:
        ReceiptListResponse with paginated receipts.
    """
    # Build base query with eager loading
    stmt = select(Receipt).options(
        selectinload(Receipt.category),
        selectinload(Receipt.tags),
    )

    # Apply filters
    if request.status:
        try:
            status_enum = ReceiptStatus(request.status)
            stmt = stmt.where(Receipt.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}",
            )

    if request.category_id:
        stmt = stmt.where(Receipt.category_id == request.category_id)

    if request.date_from:
        stmt = stmt.where(Receipt.receipt_date >= request.date_from)

    if request.date_to:
        stmt = stmt.where(Receipt.receipt_date <= request.date_to)

    # Order by receipt_date descending (newest first), then by id
    stmt = stmt.order_by(Receipt.receipt_date.desc().nullslast(), Receipt.id.desc())

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (request.page - 1) * request.page_size
    stmt = stmt.offset(offset).limit(request.page_size)

    # Execute query
    result = await session.execute(stmt)
    receipts = result.scalars().all()

    # Convert to response items
    items = []
    for receipt in receipts:
        category_name = receipt.category.name if receipt.category else None
        tag_names = [tag.name for tag in receipt.tags] if receipt.tags else []

        items.append(
            ReceiptResponse(
                id=receipt.id,
                original_filename=receipt.original_filename,
                stored_filename=receipt.stored_filename,
                file_path=receipt.file_path,
                file_size=receipt.file_size,
                mime_type=receipt.mime_type,
                image_hash=receipt.image_hash,
                ocr_text=receipt.ocr_text,
                ocr_confidence=receipt.ocr_confidence,
                ocr_language=receipt.ocr_language,
                receipt_date=receipt.receipt_date,
                store_name=receipt.store_name,
                total_amount=receipt.total_amount,
                tax_amount=receipt.tax_amount,
                currency=receipt.currency,
                category_id=receipt.category_id,
                category_name=category_name,
                category_confidence=receipt.category_confidence,
                ai_comment=receipt.ai_comment,
                ai_model=receipt.ai_model,
                ai_confidence=receipt.ai_confidence,
                status=receipt.status.value,
                status_message=receipt.status_message,
                processing_started_at=receipt.processing_started_at,
                processing_completed_at=receipt.processing_completed_at,
                retry_count=receipt.retry_count,
                tags=tag_names,
                created_at=receipt.created_at,
                updated_at=receipt.updated_at,
            )
        )

    return ReceiptListResponse.create(
        items=items,
        total=total,
        page=request.page,
        page_size=request.page_size,
    )


@router.get(
    "/{receipt_id}",
    response_model=ReceiptDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート詳細取得",
    description="指定されたレシートの詳細情報を取得します。",
)
async def get_receipt(
    receipt_id: int,
    session=Depends(get_db_session_dep),
) -> ReceiptDetailResponse:
    """Get receipt detail by ID.

    Implements RULE-BE-006.

    Args:
        receipt_id: Receipt ID.
        session: Database session.

    Returns:
        ReceiptDetailResponse.

    Raises:
        HTTPException: If receipt not found.
    """
    stmt = (
        select(Receipt)
        .options(
            selectinload(Receipt.category),
            selectinload(Receipt.tags),
        )
        .where(Receipt.id == receipt_id)
    )

    result = await session.execute(stmt)
    receipt = result.scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    category_name = receipt.category.name if receipt.category else None
    tag_names = [tag.name for tag in receipt.tags] if receipt.tags else []

    return ReceiptDetailResponse(
        id=receipt.id,
        original_filename=receipt.original_filename,
        stored_filename=receipt.stored_filename,
        file_path=receipt.file_path,
        file_size=receipt.file_size,
        mime_type=receipt.mime_type,
        image_hash=receipt.image_hash,
        ocr_text=receipt.ocr_text,
        ocr_confidence=receipt.ocr_confidence,
        ocr_language=receipt.ocr_language,
        receipt_date=receipt.receipt_date,
        store_name=receipt.store_name,
        total_amount=receipt.total_amount,
        tax_amount=receipt.tax_amount,
        currency=receipt.currency,
        category_id=receipt.category_id,
        category_name=category_name,
        category_confidence=receipt.category_confidence,
        ai_comment=receipt.ai_comment,
        ai_model=receipt.ai_model,
        ai_confidence=receipt.ai_confidence,
        status=receipt.status.value,
        status_message=receipt.status_message,
        processing_started_at=receipt.processing_started_at,
        processing_completed_at=receipt.processing_completed_at,
        retry_count=receipt.retry_count,
        tags=tag_names,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
    )


@router.get(
    "/{receipt_id}/image",
    response_model=ReceiptImageResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート画像取得",
    description="指定されたレシートの画像URLを取得します。",
)
async def get_receipt_image(
    receipt_id: int,
    session=Depends(get_db_session_dep),
) -> ReceiptImageResponse:
    """Get receipt image URL.

    Implements RULE-BE-007.

    Args:
        receipt_id: Receipt ID.
        session: Database session.

    Returns:
        ReceiptImageResponse with image URL.

    Raises:
        HTTPException: If receipt not found.
    """
    receipt = await session.get(Receipt, receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    # Construct image URL (relative path that frontend can use)
    image_url = f"/api/v1/files/{receipt.stored_filename}"

    return ReceiptImageResponse(
        receipt_id=receipt.id,
        image_url=image_url,
        mime_type=receipt.mime_type,
        file_size=receipt.file_size,
    )


@router.post(
    "/{receipt_id}/reprocess",
    response_model=ReceiptReprocessResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート再解析",
    description="指定されたレシートを再解析します（OCR・AI解析の再実行）。",
)
async def reprocess_receipt(
    receipt_id: int,
    request: ReceiptReprocessRequest,
    session=Depends(get_db_session_dep),
) -> ReceiptReprocessResponse:
    """Reprocess a receipt (re-run OCR and AI analysis).

    Args:
        receipt_id: Receipt ID.
        request: Reprocess request with force flag.
        session: Database session.

    Returns:
        ReceiptReprocessResponse with result.

    Raises:
        HTTPException: If receipt not found.
    """
    receipt = await session.get(Receipt, receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    # Reset receipt status to pending for reprocessing
    receipt.status = ReceiptStatus.PENDING
    receipt.status_message = None
    receipt.ocr_text = None
    receipt.ocr_confidence = None
    receipt.ocr_language = None
    receipt.receipt_date = None
    receipt.store_name = None
    receipt.total_amount = None
    receipt.tax_amount = None
    receipt.currency = "JPY"
    receipt.category_id = None
    receipt.category_name = None
    receipt.category_confidence = None
    receipt.ai_comment = None
    receipt.ai_model = None
    receipt.ai_confidence = None
    receipt.processing_started_at = None
    receipt.processing_completed_at = None
    receipt.retry_count = 0

    await session.commit()
    await session.refresh(receipt)

    logger.info("Receipt queued for reprocessing", extra={"receipt_id": receipt_id})

    return ReceiptReprocessResponse(
        success=True,
        receipt_id=receipt_id,
        message=f"Receipt {receipt_id} queued for reprocessing",
    )


@router.delete(
    "/{receipt_id}",
    response_model=ReceiptDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート削除",
    description="指定されたレシートを削除します。",
)
async def delete_receipt(
    receipt_id: int,
    session=Depends(get_db_session_dep),
) -> ReceiptDeleteResponse:
    """Delete a receipt.

    Args:
        receipt_id: Receipt ID.
        session: Database session.

    Returns:
        ReceiptDeleteResponse with result.

    Raises:
        HTTPException: If receipt not found.
    """
    receipt = await session.get(Receipt, receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    await session.delete(receipt)
    await session.commit()

    logger.info("Receipt deleted", extra={"receipt_id": receipt_id})

    return ReceiptDeleteResponse(
        success=True,
        receipt_id=receipt_id,
        message=f"Receipt {receipt_id} deleted successfully",
    )