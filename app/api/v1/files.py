"""API endpoints for file operations (upload and serve).

Implements RULE-FLOW-001: File management for receipt processing.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.v1.dependencies import get_db_session_dep
from app.core.config import Settings
from app.core.logging import get_logger
from app.state import get_app_state

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


async def get_settings_dep() -> Settings | None:
    """Get settings from app state."""
    return get_app_state().settings


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="レシート画像アップロード",
    description="レシート画像を未解析フォルダにアップロードします。",
)
async def upload_file(
    file: UploadFile = File(...),
    settings: Annotated[Settings | None, Depends(get_settings_dep)] = None,
) -> dict:
    """Upload a receipt image to the unparsed folder.

    Args:
        file: Uploaded image file.
        settings: Application settings.

    Returns:
        Dict with upload result.

    Raises:
        HTTPException: If file type is not supported or upload fails.
    """
    # Validate file type
    allowed_mime_types = ["image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"]
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(allowed_mime_types)}",
        )

    # Get unparsed directory from settings
    unparsed_dir = Path(settings.unparsed_dir) if settings else Path("./unparsed")
    unparsed_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    import uuid
    from datetime import datetime

    ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = unparsed_dir / unique_name

    # Save file
    try:
        content = await file.read()
        file_path.write_bytes(content)
        logger.info("File uploaded", extra={"filename": unique_name, "size": len(content)})
    except Exception as e:
        logger.exception("File upload failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e}",
        )

    return {
        "success": True,
        "filename": unique_name,
        "path": str(file_path),
        "size": len(content),
        "mime_type": file.content_type,
    }


@router.get(
    "/{path:path}",
    summary="レシート画像取得",
    description="承認済み・未解析・失敗フォルダから画像を配信します。",
    response_class=FileResponse,
)
async def serve_file(
    path: str,
    settings: Annotated[Settings | None, Depends(get_settings_dep)] = None,
) -> FileResponse:
    """Serve a file from the configured directories.

    Searches in approved, unparsed, and failed directories.

    Args:
        path: Relative file path.
        settings: Application settings.

    Returns:
        FileResponse with the image.

    Raises:
        HTTPException: If file not found.
    """
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings not configured",
        )

    # Search in multiple directories
    search_dirs = [
        Path(settings.approved_dir),
        Path(settings.unparsed_dir),
        Path(settings.failed_dir),
    ]

    for base_dir in search_dirs:
        file_path = base_dir / path
        # Security: ensure path is within base directory
        try:
            file_path.resolve().relative_to(base_dir.resolve())
        except ValueError:
            continue  # Path traversal attempt

        if file_path.exists() and file_path.is_file():
            return FileResponse(
                path=file_path,
                media_type="image/jpeg",  # Default, actual type detected by browser
                filename=file_path.name,
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"File not found: {path}",
    )