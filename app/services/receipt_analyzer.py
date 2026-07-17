"""Receipt Analyzer Orchestration Service.

Orchestrates the complete receipt analysis pipeline:
OCR -> AI Analysis -> Category Classification -> Result Assembly

Implements RULE-BE-003: Receipt image analysis (date, store, amount, category, tags, AI comment).
Implements RULE-BE-004: OCR processing implementation.
Implements RULE-BE-005: Category classification logic.
Implements RULE-BE-012: AI analysis API retry logic (RULE-ERR-001).
Implements RULE-ERR-001: Retry on failure, move to failed folder on 3 retries, notify WebUI.
Implements RULE-ERR-008: OCR text detection failure handling.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.
"""

import asyncio
import hashlib
import logging
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.constants import AccountCategory, ReceiptStatus
from app.core.logging import get_logger
from app.models.receipt import Receipt
from app.services.ai_analysis_service import AIAnalysisService, AIAnalysisResponse, ReceiptData
from app.services.category_classifier import CategoryClassifier
from app.services.ocr_service import OCRResult, OCRService

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ReceiptAnalysisResult:
    """Result of complete receipt analysis pipeline.

    Attributes:
        success: Whether the entire pipeline succeeded.
        receipt: Created Receipt model (if successful).
        ocr_result: OCR extraction result.
        ai_response: AI analysis response.
        category: Final determined category.
        category_confidence: Final category confidence.
        error: Error message if failed.
        processing_time_ms: Total processing time in milliseconds.
    """

    success: bool
    receipt: Optional[Receipt] = None
    ocr_result: Optional[OCRResult] = None
    ai_response: Optional[AIAnalysisResponse] = None
    category: Optional[AccountCategory] = None
    category_confidence: float = 0.0
    error: Optional[str] = None
    processing_time_ms: int = 0


@dataclass(frozen=True, slots=True)
class ReceiptAnalyzerConfig:
    """Configuration for ReceiptAnalyzer.

    Attributes:
        unparsed_dir: Directory for unparsed receipt images.
        unapproved_dir: Directory for unapproved (parsed, awaiting review) images.
        failed_dir: Directory for failed processing images.
        approved_dir: Directory for approved images.
        move_on_failure: Whether to move failed files to failed_dir.
        move_on_success: Whether to move successful files to unapproved_dir.
        min_ocr_confidence: Minimum OCR confidence to proceed with AI analysis.
    """

    unparsed_dir: Path
    unapproved_dir: Path
    failed_dir: Path
    approved_dir: Path
    move_on_failure: bool = True
    move_on_success: bool = True
    min_ocr_confidence: float = 10.0


class ImageFileManager:
    """Manages file operations for receipt images.

    Single responsibility: File moving, hashing, and naming operations.
    """

    def __init__(self, config: ReceiptAnalyzerConfig) -> None:
        """Initialize file manager.

        Args:
            config: Analyzer configuration with directory paths.
        """
        self._config = config
        self._settings = get_settings()

    def compute_image_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of image file.

        Args:
            file_path: Path to image file.

        Returns:
            SHA-256 hash as hex string.
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def generate_stored_filename(
        self,
        original_filename: str,
        receipt_date: Optional[datetime],
        store_name: Optional[str],
        total_amount: Optional[int],
        category: Optional[AccountCategory],
        tags: list[str],
        image_hash: str,
    ) -> str:
        """Generate stored filename for approved receipt.

        Format: YYYYMMDD_storename_amount_category_tags_hash.ext
        Implements RULE-FLOW-001-11 naming convention.

        Args:
            original_filename: Original filename (for extension).
            receipt_date: Receipt date.
            store_name: Store/merchant name.
            total_amount: Total amount in yen.
            category: Account category.
            tags: List of tags.
            image_hash: Image SHA-256 hash (first 8 chars used).

        Returns:
            Generated filename.
        """
        ext = Path(original_filename).suffix.lower()
        if ext not in self._settings.supported_image_extensions:
            ext = ".jpg"

        date_str = (
            receipt_date.strftime("%Y%m%d")
            if receipt_date
            else datetime.now().strftime("%Y%m%d")
        )
        store_clean = self._sanitize_filename(store_name or "unknown_store")
        amount_str = f"{total_amount}円" if total_amount else "0円"
        category_str = category.value if category else "その他"
        tags_str = "_".join(self._sanitize_filename(t) for t in tags[:3]) if tags else "notag"
        hash_short = image_hash[:8]

        filename = f"{date_str}_{store_clean}_{amount_str}_{category_str}_{tags_str}_{hash_short}{ext}"
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
        return text[:50]

    def move_to_failed(self, source_path: Path) -> Path:
        """Move file to failed directory.

        Implements RULE-ERR-001-2: Move to failed folder on 3 retries failure.

        Args:
            source_path: Source file path.

        Returns:
            Destination path.
        """
        self._config.failed_dir.mkdir(parents=True, exist_ok=True)
        dest_path = self._config.failed_dir / source_path.name
        # Handle name collision
        counter = 1
        while dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            dest_path = self._config.failed_dir / f"{stem}_failed_{counter}{suffix}"
            counter += 1
        shutil.move(str(source_path), str(dest_path))
        logger.info(
            "Moved file to failed directory",
            extra={"source": str(source_path), "dest": str(dest_path)},
        )
        return dest_path

    def move_to_unapproved(self, source_path: Path, new_filename: str) -> Path:
        """Move file to unapproved directory with new filename.

        Args:
            source_path: Source file path.
            new_filename: New filename.

        Returns:
            Destination path.
        """
        self._config.unapproved_dir.mkdir(parents=True, exist_ok=True)
        dest_path = self._config.unapproved_dir / new_filename
        # Handle name collision
        counter = 1
        while dest_path.exists():
            stem = Path(new_filename).stem
            suffix = Path(new_filename).suffix
            dest_path = self._config.unapproved_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        shutil.move(str(source_path), str(dest_path))
        logger.info(
            "Moved file to unapproved directory",
            extra={"source": str(source_path), "dest": str(dest_path)},
        )
        return dest_path


class ReceiptAnalyzer:
    """Orchestrates the complete receipt analysis pipeline.

    Pipeline steps:
    1. OCR text extraction (RULE-BE-004)
    2. AI analysis for structured data (RULE-BE-003, RULE-BE-012)
    3. Category classification (RULE-BE-005)
    4. Result assembly into Receipt model
    5. File management (RULE-ERR-001, RULE-FLOW-001-11)

    Implements RULE-ERR-001: Retry 3 times, move to failed folder, notify WebUI.
    Implements RULE-ERR-008: Handle OCR text detection failure gracefully.
    Single responsibility: Orchestrate services, not implement their logic.
    """

    def __init__(
        self,
        config: Optional[ReceiptAnalyzerConfig] = None,
        ocr_service: Optional[OCRService] = None,
        ai_service: Optional[AIAnalysisService] = None,
        category_classifier: Optional[CategoryClassifier] = None,
        file_manager: Optional[ImageFileManager] = None,
    ) -> None:
        """Initialize receipt analyzer with injected dependencies.

        Args:
            config: Analyzer configuration.
            ocr_service: OCR service instance.
            ai_service: AI analysis service instance.
            category_classifier: Category classifier instance.
            file_manager: File manager instance.
        """
        self._settings = get_settings()
        self._config = config or ReceiptAnalyzerConfig(
            unparsed_dir=self._settings.unparsed_dir,
            unapproved_dir=self._settings.unapproved_dir,
            failed_dir=self._settings.failed_dir,
            approved_dir=self._settings.approved_dir,
        )

        self._ocr_service = ocr_service or OCRService()
        self._ai_service = ai_service or AIAnalysisService()
        self._category_classifier = category_classifier or CategoryClassifier(ai_service=self._ai_service)
        self._file_manager = file_manager or ImageFileManager(self._config)

        logger.info(
            "Receipt analyzer initialized",
            extra={
                "unparsed_dir": str(self._config.unparsed_dir),
                "unapproved_dir": str(self._config.unapproved_dir),
                "failed_dir": str(self._config.failed_dir),
            },
        )

    async def analyze_receipt(
        self,
        image_path: Path,
        move_file: bool = True,
    ) -> ReceiptAnalysisResult:
        """Analyze a receipt image through the complete pipeline.

        Pipeline:
        1. OCR text extraction
        2. AI analysis (with retry logic per RULE-ERR-001)
        3. Category classification
        4. Receipt model creation
        5. File management

        Args:
            image_path: Path to receipt image file.
            move_file: Whether to move file on success/failure.

        Returns:
            ReceiptAnalysisResult with all extracted data.
        """
        start_time = time.perf_counter()
        logger.info("Starting receipt analysis", extra={"image_path": str(image_path)})

        try:
            # Step 1: OCR Processing (RULE-BE-004)
            ocr_result = await self._perform_ocr(image_path)

            # Handle OCR failure (RULE-ERR-008)
            if not self._ocr_service.has_text(ocr_result, self._config.min_ocr_confidence):
                logger.warning(
                    "OCR detected no meaningful text",
                    extra={
                        "path": str(image_path),
                        "confidence": ocr_result.confidence,
                        "text_length": len(ocr_result.text),
                    },
                )
                # Continue with empty OCR text - AI may still extract info from image context
                # But we note the low confidence

            # Step 2: AI Analysis (RULE-BE-003, RULE-BE-012, RULE-ERR-001)
            ai_response = await self._ai_service.analyze_receipt(
                ocr_text=ocr_result.text,
                image_path=str(image_path),
            )

            if not ai_response.success:
                # AI analysis failed after retries
                error_msg = ai_response.error or "AI analysis failed"
                logger.error(
                    "AI analysis failed after retries",
                    extra={"path": str(image_path), "error": error_msg},
                )

                if move_file and self._config.move_on_failure:
                    self._file_manager.move_to_failed(image_path)

                return ReceiptAnalysisResult(
                    success=False,
                    ocr_result=ocr_result,
                    ai_response=ai_response,
                    error=error_msg,
                    processing_time_ms=int((time.perf_counter() - start_time) * 1000),
                )

            # Step 3: Category Classification (RULE-BE-005)
            ai_data = ai_response.data
            if ai_data is None:
                error_msg = "AI analysis succeeded but returned no data"
                logger.error(error_msg, extra={"path": str(image_path)})
                if move_file and self._config.move_on_failure:
                    self._file_manager.move_to_failed(image_path)
                return ReceiptAnalysisResult(
                    success=False,
                    ocr_result=ocr_result,
                    ai_response=ai_response,
                    error=error_msg,
                    processing_time_ms=int((time.perf_counter() - start_time) * 1000),
                )

            # Classify category using best available method
            category, category_confidence = await self._category_classifier.classify(
                store_name=ai_data.store_name,
                total_amount=ai_data.total_amount,
                ocr_text=ocr_result.text,
                ai_category=ai_data.category,
                ai_confidence=ai_data.category_confidence,
            )

            # Step 4: Build Receipt Model
            receipt = self._build_receipt_model(
                image_path=image_path,
                ocr_result=ocr_result,
                ai_data=ai_data,
                category=category,
                category_confidence=category_confidence,
                ai_response=ai_response,
            )

            # Step 5: File Management
            if move_file and self._config.move_on_success:
                new_filename = self._file_manager.generate_stored_filename(
                    original_filename=image_path.name,
                    receipt_date=receipt.receipt_date,
                    store_name=receipt.store_name,
                    total_amount=receipt.total_amount,
                    category=category,
                    tags=ai_data.tags,
                    image_hash=receipt.image_hash,
                )
                new_path = self._file_manager.move_to_unapproved(image_path, new_filename)
                receipt.stored_filename = new_filename
                receipt.file_path = str(new_path)

            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "Receipt analysis completed successfully",
                extra={
                    "path": str(image_path),
                    "store": receipt.store_name,
                    "amount": receipt.total_amount,
                    "category": category.value if category else None,
                    "processing_time_ms": processing_time_ms,
                },
            )

            return ReceiptAnalysisResult(
                success=True,
                receipt=receipt,
                ocr_result=ocr_result,
                ai_response=ai_response,
                category=category,
                category_confidence=category_confidence,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            logger.exception(
                "Unexpected error during receipt analysis",
                extra={"path": str(image_path), "error": str(e)},
            )
            if move_file and self._config.move_on_failure:
                self._file_manager.move_to_failed(image_path)
            return ReceiptAnalysisResult(
                success=False,
                error=f"Analysis failed: {e}",
                processing_time_ms=int((time.perf_counter() - start_time) * 1000),
            )

    async def _perform_ocr(self, image_path: Path) -> OCRResult:
        """Perform OCR with graceful failure handling.

        Implements RULE-ERR-008: Returns empty result instead of raising on failure.

        Args:
            image_path: Path to image file.

        Returns:
            OCRResult (empty on failure).
        """
        return self._ocr_service.extract_text_with_fallback(image_path)

    def _build_receipt_model(
        self,
        image_path: Path,
        ocr_result: OCRResult,
        ai_data: ReceiptData,
        category: Optional[AccountCategory],
        category_confidence: float,
        ai_response: AIAnalysisResponse,
    ) -> Receipt:
        """Build Receipt model from analysis results.

        Args:
            image_path: Original image path.
            ocr_result: OCR extraction result.
            ai_data: AI extracted data.
            category: Final classified category.
            category_confidence: Category confidence.
            ai_response: Full AI response.

        Returns:
            Receipt model instance.
        """
        # Compute image hash
        image_hash = self._file_manager.compute_image_hash(image_path)

        # Parse date
        receipt_date = None
        if ai_data.receipt_date:
            try:
                receipt_date = datetime.fromisoformat(ai_data.receipt_date.replace("Z", "+00:00"))
            except ValueError:
                logger.warning("Failed to parse receipt date", extra={"date": ai_data.receipt_date})

        # Create receipt model
        receipt = Receipt(
            original_filename=image_path.name,
            stored_filename=image_path.name,  # Will be updated after move
            file_path=str(image_path),
            file_size=image_path.stat().st_size,
            mime_type=self._guess_mime_type(image_path),
            image_hash=image_hash,
            ocr_text=ocr_result.text if ocr_result.text else None,
            ocr_confidence=ocr_result.confidence if ocr_result.confidence > 0 else None,
            ocr_language=ocr_result.language,
            receipt_date=receipt_date,
            store_name=ai_data.store_name,
            total_amount=ai_data.total_amount,
            tax_amount=ai_data.tax_amount,
            currency=ai_data.currency,
            category_id=None,  # Will be set when category is linked
            category_confidence=category_confidence,
            ai_comment=ai_data.ai_comment,
            ai_model=ai_response.model,
            ai_confidence=ai_data.ai_confidence,
            status=ReceiptStatus.UNAPPROVED,
            status_message="解析完了、承認待ち" if ai_response.success else "解析に問題あり",
        )

        return receipt

    def _guess_mime_type(self, image_path: Path) -> str:
        """Guess MIME type from file extension.

        Args:
            image_path: Image file path.

        Returns:
            MIME type string.
        """
        ext = image_path.suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".bmp": "image/bmp",
        }
        return mime_map.get(ext, "application/octet-stream")

    async def close(self) -> None:
        """Close all service connections."""
        await self._ai_service.close()
        logger.info("Receipt analyzer closed")

    async def __aenter__(self) -> "ReceiptAnalyzer":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


async def get_receipt_analyzer() -> ReceiptAnalyzer:
    """Get receipt analyzer instance (dependency injection helper).

    Returns:
        ReceiptAnalyzer instance.
    """
    return ReceiptAnalyzer()