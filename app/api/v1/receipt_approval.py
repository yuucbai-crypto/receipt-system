"""API endpoints for receipt approval/rejection.

Implements RULE-FLOW-001-11: Rejection reason registration on rejection.
Implements RULE-FLOW-001-12: File renaming on approval.
Implements RULE-BE-018: Rejection reason data persistence.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.v1.dependencies import get_db_session_dep
from app.schemas.receipt_approval import (
    ReceiptApprovalRequest,
    ReceiptApprovalResponse,
    ReceiptRejectRequest,
    RejectionReasonListResponse,
    RejectionReasonResponse,
)
from app.core.logging import get_logger
from app.models.receipt import Receipt, ReceiptStatus
from app.models.rejection_reason import RejectionReason
from app.services.file_sorting_service import FileSortingService, get_file_sorting_service
from app.services.rejection_reason_service import (
    RejectionReasonService,
    RejectionData,
    get_rejection_reason_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/receipt-approval", tags=["Receipt Approval"])


@router.post(
    "/approve",
    response_model=ReceiptApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート承認",
    description="レシートを承認し、ファイルを承認済みフォルダへ仕分けします。",
)
async def approve_receipt(
    request: ReceiptApprovalRequest,
    session = Depends(get_db_session_dep),
    file_service: FileSortingService = Depends(get_file_sorting_service),
) -> ReceiptApprovalResponse:
    """Approve a receipt and sort its file.

    Implements RULE-FLOW-001-12 and RULE-FLOW-001-13.

    Args:
        request: Approval request.
        session: Database session.
        file_service: File sorting service.

    Returns:
        ReceiptApprovalResponse with updated receipt info.

    Raises:
        HTTPException: If receipt not found or already approved.
    """
    receipt = await session.get(Receipt, request.receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {request.receipt_id} not found",
        )

    if receipt.status == ReceiptStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Receipt {request.receipt_id} is already approved",
        )

    if receipt.status == ReceiptStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve rejected receipt {request.receipt_id}",
        )

    # Update receipt status
    receipt.status = ReceiptStatus.APPROVED
    receipt.status_message = "承認済み"
    receipt.processing_completed_at = datetime.now(timezone.utc)

    await session.commit()

    # Sort file to approved directory
    sort_result = file_service.sort_approved_receipt(receipt)

    if sort_result.success:
        receipt.file_path = str(sort_result.destination_path)
        receipt.stored_filename = sort_result.new_filename
        await session.commit()
        logger.info(
            "Receipt approved and file sorted",
            extra={
                "receipt_id": receipt.id,
                "new_filename": sort_result.new_filename,
                "destination": str(sort_result.destination_path),
            },
        )
    else:
        logger.warning(
            "Receipt approved but file sort failed",
            extra={
                "receipt_id": receipt.id,
                "error": sort_result.error,
            },
        )

    return ReceiptApprovalResponse(
        receipt_id=receipt.id,
        status=receipt.status.value,
        status_message=receipt.status_message,
        rejection_reason_id=None,
        updated_at=receipt.updated_at,
    )


@router.post(
    "/reject",
    response_model=ReceiptApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="レシート却下",
    description="レシートを却下し、却下理由を保存します。",
)
async def reject_receipt(
    request: ReceiptRejectRequest,
    session = Depends(get_db_session_dep),
    rejection_service: RejectionReasonService = Depends(get_rejection_reason_service),
) -> ReceiptApprovalResponse:
    """Reject a receipt with reason.

    Implements RULE-FLOW-001-11 and RULE-BE-018.

    Args:
        request: Rejection request with reason.
        session: Database session.
        rejection_service: Rejection reason service.

    Returns:
        ReceiptApprovalResponse with rejection reason ID.

    Raises:
        HTTPException: If receipt not found or already rejected.
    """
    receipt = await session.get(Receipt, request.receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {request.receipt_id} not found",
        )

    if receipt.status == ReceiptStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Receipt {request.receipt_id} is already rejected",
        )

    # Create rejection reason
    rejection_data = RejectionData(
        receipt_id=request.receipt_id,
        reason_code=request.reason_code,
        reason_text=request.reason_text,
        user_note=request.user_note,
        is_for_ai_training=request.is_for_ai_training,
    )

    result = await rejection_service.create_rejection_reason(rejection_data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rejection reason: {result.error}",
        )

    # Update receipt status
    receipt.status = ReceiptStatus.REJECTED
    receipt.status_message = f"却下: {request.reason_text}"

    await session.commit()

    logger.info(
        "Receipt rejected",
        extra={
            "receipt_id": request.receipt_id,
            "rejection_reason_id": result.rejection_reason_id,
            "reason_code": request.reason_code,
        },
    )

    return ReceiptApprovalResponse(
        receipt_id=receipt.id,
        status=receipt.status.value,
        status_message=receipt.status_message,
        rejection_reason_id=result.rejection_reason_id,
        updated_at=receipt.updated_at,
    )


@router.get(
    "/rejection-reasons/{receipt_id}",
    response_model=RejectionReasonResponse,
    status_code=status.HTTP_200_OK,
    summary="却下理由取得",
    description="指定されたレシートの却下理由を取得します。",
)
async def get_rejection_reason(
    receipt_id: int,
    session = Depends(get_db_session_dep),
    rejection_service: RejectionReasonService = Depends(get_rejection_reason_service),
) -> RejectionReasonResponse:
    """Get rejection reason for a receipt.

    Args:
        receipt_id: Receipt ID.
        session: Database session.
        rejection_service: Rejection reason service.

    Returns:
        RejectionReasonResponse.

    Raises:
        HTTPException: If rejection reason not found.
    """
    reason = await rejection_service.get_rejection_reason(receipt_id)
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rejection reason for receipt {receipt_id} not found",
        )

    return RejectionReasonResponse.model_validate(reason)


@router.get(
    "/rejection-reasons",
    response_model=RejectionReasonListResponse,
    status_code=status.HTTP_200_OK,
    summary="却下理由一覧取得",
    description="却下理由の一覧を取得します（フィルタ・ページング対応）。",
)
async def list_rejection_reasons(
    category: str | None = None,
    reason_code: str | None = None,
    is_for_ai_training: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    session = Depends(get_db_session_dep),
    rejection_service: RejectionReasonService = Depends(get_rejection_reason_service),
) -> RejectionReasonListResponse:
    """List rejection reasons with filtering and pagination.

    Args:
        category: Filter by category.
        reason_code: Filter by reason code.
        is_for_ai_training: Filter by AI training flag.
        page: Page number.
        page_size: Page size.
        session: Database session.
        rejection_service: Rejection reason service.

    Returns:
        RejectionReasonListResponse.
    """
    from app.services.rejection_reason_service import RejectionCategory

    cat = RejectionCategory(category) if category else None

    reasons = await rejection_service.get_rejection_reasons(
        category=cat,
        reason_code=reason_code,
        is_for_ai_training=is_for_ai_training,
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    # Get total count
    from sqlalchemy import func

    total_stmt = select(func.count(RejectionReason.id))
    if cat:
        total_stmt = total_stmt.where(RejectionReason.reason_category == cat.value)
    if reason_code:
        total_stmt = total_stmt.where(RejectionReason.reason_code == reason_code)
    if is_for_ai_training is not None:
        total_stmt = total_stmt.where(RejectionReason.is_for_ai_training == is_for_ai_training)

    total_result = await session.execute(total_stmt)
    total = total_result.scalar() or 0

    return RejectionReasonListResponse(
        items=[RejectionReasonResponse.model_validate(r) for r in reasons],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )