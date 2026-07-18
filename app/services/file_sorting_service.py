"""File Sorting Service for approved receipt file management.

Implements RULE-BE-011: File renaming and auto-sorting on approval.
Implements RULE-FLOW-001-12: File naming format YYYY-MM-DD_店舗名_金額円.jpg
Implements RULE-FLOW-001-13: Auto-sorting by category/tag with year-month folders.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.
"""

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.constants import AccountCategory
from app.core.logging import get_logger
from app.models.receipt import Receipt

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class FileSortingConfig:
    """Configuration for file sorting service.

    Attributes:
        approved_dir: Base directory for approved receipts.
        create_year_month_folders: Whether to create YYYY-MM subdirectories.
    """

    approved_dir: Path
    create_year_month_folders: bool = True


@dataclass(frozen=True, slots=True)
class FileSortResult:
    """Result of file sorting operation.

    Attributes:
        success: Whether sorting succeeded.
        source_path: Original file path.
        destination_path: Final destination path.
        new_filename: Generated filename.
        category_folder: Category folder name used.
        year_month_folder: Year-month folder name used.
        error: Error message if failed.
    """

    success: bool
    source_path: Path
    destination_path: Path | None = None
    new_filename: str | None = None
    category_folder: str | None = None
    year_month_folder: str | None = None
    error: str | None = None


class FileSortingService:
    """Service for renaming and sorting approved receipt files.

    Single responsibility: File naming and directory organization
    for approved receipts.
    """

    def __init__(
        self,
        config: FileSortingConfig | None = None,
    ) -> None:
        """Initialize file sorting service.

        Args:
            config: File sorting configuration.
        """
        settings = get_settings()
        self._config = config or FileSortingConfig(
            approved_dir=settings.approved_dir,
            create_year_month_folders=True,
        )
        self._settings = settings

    def generate_approved_filename(
        self,
        receipt: Receipt,
    ) -> str:
        """Generate approved filename per RULE-FLOW-001-12.

        Format: YYYY-MM-DD_店舗名_金額円.jpg
        Note: Uses YYYY-MM-DD format (with hyphens) as per requirement,
        not the YYYYMMDD format used in unapproved naming.

        Args:
            receipt: Approved receipt model.

        Returns:
            Generated filename with extension.
        """
        # Get date
        if receipt.receipt_date:
            date_str = receipt.receipt_date.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Get store name (sanitized)
        store_name = self._sanitize_filename(receipt.store_name or "不明店舗")

        # Get amount
        amount_str = f"{receipt.total_amount}円" if receipt.total_amount else "0円"

        # Get extension from original file
        ext = Path(receipt.original_filename).suffix.lower()
        if ext not in self._settings.supported_image_extensions:
            ext = ".jpg"

        # Construct filename: YYYY-MM-DD_店舗名_金額円.jpg
        filename = f"{date_str}_{store_name}_{amount_str}{ext}"

        logger.debug(
            "Generated approved filename",
            extra={
                "receipt_id": receipt.id,
                "filename": filename,
                "date_str": date_str,
                "store_name": store_name,
                "amount_str": amount_str,
            },
        )

        return filename

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename.

        Args:
            text: Text to sanitize.

        Returns:
            Sanitized text safe for filenames.
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, "_")

        # Limit length
        return text[:100]

    def _get_category_folder(self, receipt: Receipt) -> str:
        """Get category folder name from receipt.

        Args:
            receipt: Receipt model.

        Returns:
            Category folder name.
        """
        if receipt.category_id is not None:
            # In a real implementation, we'd fetch the category name
            # For now, use a placeholder or category code
            return f"category_{receipt.category_id}"

        # Fallback to 'その他' (Other)
        return AccountCategory.OTHER.value

    def _get_year_month_folder(self, receipt: Receipt) -> str:
        """Get year-month folder name from receipt date.

        Format: YYYY-MM

        Args:
            receipt: Receipt model.

        Returns:
            Year-month folder string.
        """
        if receipt.receipt_date:
            return receipt.receipt_date.strftime("%Y-%m")
        return datetime.now().strftime("%Y-%m")

    def _build_destination_path(
        self,
        receipt: Receipt,
        filename: str,
    ) -> Path:
        """Build full destination path for approved receipt.

        Structure: approved_dir/カテゴリ/YYYY-MM/filename

        Args:
            receipt: Receipt model.
            filename: Generated filename.

        Returns:
            Full destination path.
        """
        category_folder = self._get_category_folder(receipt)
        year_month_folder = self._get_year_month_folder(receipt)

        dest_dir = self._config.approved_dir / category_folder / year_month_folder
        return dest_dir / filename

    def sort_approved_receipt(
        self,
        receipt: Receipt,
        source_path: Path | None = None,
    ) -> FileSortResult:
        """Move and rename approved receipt file to organized location.

        Implements RULE-FLOW-001-12 and RULE-FLOW-001-13.

        Args:
            receipt: Approved receipt model.
            source_path: Source file path (defaults to receipt.file_path).

        Returns:
            FileSortResult with operation details.
        """
        src = source_path or Path(receipt.file_path)

        if not src.exists():
            logger.error(
                "Source file not found for sorting",
                extra={"receipt_id": receipt.id, "source_path": str(src)},
            )
            return FileSortResult(
                success=False,
                source_path=src,
                error=f"Source file not found: {src}",
            )

        try:
            # Generate new filename
            new_filename = self.generate_approved_filename(receipt)

            # Build destination path
            dest_path = self._build_destination_path(receipt, new_filename)

            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle filename collision
            final_dest = self._resolve_collision(dest_path)

            # Move file
            shutil.move(str(src), str(final_dest))

            logger.info(
                "Receipt file sorted successfully",
                extra={
                    "receipt_id": receipt.id,
                    "source": str(src),
                    "destination": str(final_dest),
                    "category": self._get_category_folder(receipt),
                    "year_month": self._get_year_month_folder(receipt),
                },
            )

            return FileSortResult(
                success=True,
                source_path=src,
                destination_path=final_dest,
                new_filename=new_filename,
                category_folder=self._get_category_folder(receipt),
                year_month_folder=self._get_year_month_folder(receipt),
            )

        except OSError as e:
            logger.exception(
                "Failed to sort receipt file",
                extra={"receipt_id": receipt.id, "error": str(e)},
            )
            return FileSortResult(
                success=False,
                source_path=src,
                error=f"File operation failed: {e}",
            )
        except Exception as e:
            logger.exception(
                "Unexpected error during file sorting",
                extra={"receipt_id": receipt.id, "error": str(e)},
            )
            return FileSortResult(
                success=False,
                source_path=src,
                error=f"Unexpected error: {e}",
            )

    def _resolve_collision(self, dest_path: Path) -> Path:
        """Resolve filename collision by appending counter.

        Args:
            dest_path: Desired destination path.

        Returns:
            Non-conflicting path.
        """
        if not dest_path.exists():
            return dest_path

        stem = dest_path.stem
        suffix = dest_path.suffix
        parent = dest_path.parent
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def get_approved_file_path(self, receipt: Receipt) -> Path:
        """Get the expected approved file path for a receipt.

        Useful for checking if file exists or constructing URLs.

        Args:
            receipt: Receipt model.

        Returns:
            Expected file path.
        """
        filename = self.generate_approved_filename(receipt)
        return self._build_destination_path(receipt, filename)

    def list_approved_files(
        self,
        category: str | None = None,
        year_month: str | None = None,
    ) -> list[Path]:
        """List approved receipt files with optional filtering.

        Args:
            category: Filter by category folder name.
            year_month: Filter by year-month folder (YYYY-MM).

        Returns:
            List of file paths.
        """
        search_dir = self._config.approved_dir

        if category:
            search_dir = search_dir / category
        if year_month:
            search_dir = search_dir / year_month

        if not search_dir.exists():
            return []

        files = []
        for ext in self._settings.supported_image_extensions:
            files.extend(search_dir.rglob(f"*{ext}"))

        return sorted(files)


def get_file_sorting_service() -> FileSortingService:
    """Dependency injection helper for FileSortingService.

    Returns:
        FileSortingService instance.
    """
    return FileSortingService()