"""API endpoints for file management (approved receipt sorting).

Implements RULE-FLOW-001-12: File renaming on approval.
Implements RULE-FLOW-001-13: Auto-sorting by category/year-month.
Implements RULE-BE-011: File management API.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db_session_dep
from app.schemas.file_management import (
    ApprovedFileInfo,
    ApprovedFileListRequest,
    ApprovedFileListResponse,
    FileSortRequest,
    FileSortResponse,
)
from app.core.logging import get_logger
from app.models.receipt import Receipt, ReceiptStatus
from app.services.file_sorting_service import FileSortingService, get_file_sorting_service

logger = get_logger(__name__)

router = APIRouter(prefix="/file-management", tags=["File Management"])


@router.post(
    "/sort-approved",
    response_model=FileSortResponse,
    status_code=status.HTTP_200_OK,
    summary="承認済みレシートのファイル仕分け実行",
    description="承認済みレシートのファイルをリネームし、勘定科目・年月フォルダに仕分けします。",
)
async def sort_approved_receipt(
    request: FileSortRequest,
    session: AsyncSession = Depends(get_db_session_dep),
    service: FileSortingService = Depends(get_file_sorting_service),
) -> FileSortResponse:
    """Sort and rename approved receipt file.

    Implements RULE-FLOW-001-12 and RULE-FLOW-001-13.

    Args:
        request: File sort request with receipt ID.
        session: Database session.
        service: File sorting service.

    Returns:
        FileSortResponse with operation result.

    Raises:
        HTTPException: If receipt not found or not approved.
    """
    # Verify receipt exists and is approved
    receipt = await session.get(Receipt, request.receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {request.receipt_id} not found",
        )

    if receipt.status != ReceiptStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Receipt {request.receipt_id} is not approved (status: {receipt.status.value})",
        )

    # Execute file sort
    result = service.sort_approved_receipt(receipt)

    # Update receipt with new file path if successful
    if result.success and result.destination_path:
        receipt.file_path = str(result.destination_path)  # type: ignore[assignment]
        receipt.stored_filename = result.new_filename  # type: ignore[assignment]
        await session.commit()

    return FileSortResponse(
        success=result.success,
        receipt_id=receipt.id,
        source_path=str(result.source_path),
        destination_path=str(result.destination_path) if result.destination_path else None,
        new_filename=result.new_filename,
        category_folder=result.category_folder,
        year_month_folder=result.year_month_folder,
        error=result.error,
    )


@router.post(
    "/list-approved",
    response_model=ApprovedFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="承認済みファイル一覧取得",
    description="承認済みフォルダ内のファイル一覧を取得します（カテゴリ・年月でフィルタ可）。",
)
async def list_approved_files(
    request: ApprovedFileListRequest,
    service: FileSortingService = Depends(get_file_sorting_service),
) -> ApprovedFileListResponse:
    """List approved receipt files with optional filtering.

    Args:
        request: List request with optional filters.
        service: File sorting service.

    Returns:
        ApprovedFileListResponse with paginated file list.
    """
    files = service.list_approved_files(
        category=request.category,
        year_month=request.year_month,
    )

    # Pagination
    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    paginated = files[start:end]

    # Build file info list
    items = []
    for f in paginated:
        stat = f.stat()
        # Extract category and year_month from path
        rel_path = f.relative_to(service._config.approved_dir)
        parts = rel_path.parts
        category_folder = parts[0] if len(parts) > 1 else ""
        year_month_folder = parts[1] if len(parts) > 2 else ""

        items.append(
            ApprovedFileInfo(
                filename=f.name,
                filepath=str(f),
                category_folder=category_folder,
                year_month_folder=year_month_folder,
                file_size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            )
        )

    return ApprovedFileListResponse(
        items=items,
        total=len(files),
        page=request.page,
        page_size=request.page_size,
        total_pages=(len(files) + request.page_size - 1) // request.page_size,
    )


@router.get(
    "/approved-path/{receipt_id}",
    response_model=FileSortResponse,
    status_code=status.HTTP_200_OK,
    summary="承認済みファイルの期待パス取得",
    description="承認済みレシートの期待されるファイルパスを取得します（ファイル存在確認用）。",
)
async def get_approved_file_path(
    receipt_id: int,
    session: AsyncSession = Depends(get_db_session_dep),
    service: FileSortingService = Depends(get_file_sorting_service),
) -> FileSortResponse:
    """Get expected approved file path for a receipt.

    Args:
        receipt_id: Receipt ID.
        session: Database session.
        service: File sorting service.

    Returns:
        FileSortResponse with expected path.

    Raises:
        HTTPException: If receipt not found.
    """
    receipt = await session.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )

    path = service.get_approved_file_path(receipt)
    exists = path.exists()

    return FileSortResponse(
        success=True,
        receipt_id=receipt.id,
        source_path="",
        destination_path=str(path),
        new_filename=path.name,
        category_folder=service._get_category_folder(receipt),
        year_month_folder=service._get_year_month_folder(receipt),
        error=None if exists else "File does not exist at expected path",
    )