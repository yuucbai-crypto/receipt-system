"""OCR Service for receipt image text extraction using Tesseract.

Implements RULE-BE-004: OCR processing implementation.
Implements RULE-ERR-008: OCR text detection failure handling.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OCRResult:
    """Result of OCR processing.

    Attributes:
        text: Extracted text from the image.
        confidence: Average confidence score (0.0-100.0).
        language: OCR language used.
    """

    text: str
    confidence: float
    language: str


class OCRService:
    """Service for performing OCR on receipt images.

    Single responsibility: Extract text from receipt images using Tesseract OCR
    with Japanese and English language support, including image preprocessing.

    Implements RULE-BE-004: OCR processing implementation.
    Implements RULE-ERR-008: Handles OCR text detection failures gracefully.
    """

    def __init__(self) -> None:
        """Initialize OCR service with settings."""
        self._settings = get_settings()
        self._language = self._settings.ocr_language
        self._dpi = self._settings.ocr_dpi

        # Verify Tesseract is available
        self._verify_tesseract()

        logger.info(
            "OCR service initialized",
            extra={"language": self._language, "dpi": self._dpi},
        )

    def _verify_tesseract(self) -> None:
        """Verify Tesseract is installed and accessible."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract verified", extra={"version": str(version)})
        except pytesseract.TesseractNotFoundError:
            logger.warning(
                "Tesseract not found - OCR will fail at runtime",
                extra={"hint": "Install tesseract-ocr and tesseract-ocr-jpn packages"},
            )
        except Exception as e:
            logger.warning(
                "Tesseract verification failed",
                extra={"error": str(e)},
            )

    def preprocess_image(self, image_path: Path) -> Image.Image:
        """Preprocess image for better OCR accuracy.

        Args:
            image_path: Path to the image file.

        Returns:
            Preprocessed PIL Image.

        Raises:
            FileNotFoundError: If image file does not exist.
            OSError: If image cannot be opened or processed.
        """
        logger.debug("Preprocessing image", extra={"path": str(image_path)})

        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        image = Image.open(image_path)

        # Convert to RGB if necessary (e.g., RGBA, P mode)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Resize for better DPI if image is too small
        width, height = image.size
        target_dpi = self._dpi
        scale_factor = target_dpi / 72.0
        if scale_factor > 1.0:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(
                "Resized image for DPI",
                extra={"original": (width, height), "new": (new_width, new_height)},
            )

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)

        # Convert to grayscale
        image = image.convert("L")

        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # Binarize with threshold
        threshold = 128
        image = image.point(lambda p: 255 if p > threshold else 0)

        logger.debug("Image preprocessing completed", extra={"final_size": image.size})
        return image

    def extract_text(self, image_path: Path) -> OCRResult:
        """Extract text from receipt image using Tesseract OCR.

        Args:
            image_path: Path to the receipt image file.

        Returns:
            OCRResult containing extracted text and confidence.

        Raises:
            FileNotFoundError: If image file does not exist.
            OSError: If image cannot be processed.
            pytesseract.TesseractError: If Tesseract execution fails.
        """
        logger.info("Starting OCR extraction", extra={"path": str(image_path)})

        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)

            # Perform OCR with detailed output
            ocr_data = pytesseract.image_to_data(
                processed_image,
                lang=self._language,
                output_type=pytesseract.Output.DICT,
            )

            # Extract text and calculate average confidence
            text_parts = []
            confidences = []

            for i, conf in enumerate(ocr_data["conf"]):
                if conf > 0:  # Valid confidence values are > 0
                    text = ocr_data["text"][i].strip()
                    if text:
                        text_parts.append(text)
                        confidences.append(conf)

            full_text = "\n".join(text_parts)
            avg_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

            logger.info(
                "OCR extraction completed",
                extra={
                    "path": str(image_path),
                    "text_length": len(full_text),
                    "confidence": avg_confidence,
                    "word_count": len(text_parts),
                },
            )

            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                language=self._language,
            )

        except pytesseract.TesseractNotFoundError as e:
            logger.error(
                "Tesseract not found",
                extra={"path": str(image_path), "error": str(e)},
            )
            raise OSError("Tesseract OCR engine not installed") from e
        except pytesseract.TesseractError as e:
            logger.error(
                "Tesseract execution failed",
                extra={"path": str(image_path), "error": str(e)},
            )
            raise
        except Exception as e:
            logger.error(
                "OCR extraction failed",
                extra={"path": str(image_path), "error": str(e)},
            )
            raise

    def extract_text_with_fallback(self, image_path: Path) -> OCRResult:
        """Extract text with graceful handling of OCR failures.

        Implements RULE-ERR-008: Returns empty result with zero confidence
        instead of raising on text detection failure.

        Args:
            image_path: Path to the receipt image file.

        Returns:
            OCRResult (empty text with 0 confidence on failure).
        """
        try:
            return self.extract_text(image_path)
        except (pytesseract.TesseractError, OSError, FileNotFoundError) as e:
            logger.warning(
                "OCR failed, returning empty result",
                extra={"path": str(image_path), "error": str(e)},
            )
            return OCRResult(text="", confidence=0.0, language=self._language)
        except Exception as e:
            logger.error(
                "Unexpected OCR error, returning empty result",
                extra={"path": str(image_path), "error": str(e)},
            )
            return OCRResult(text="", confidence=0.0, language=self._language)

    def has_text(self, result: OCRResult, min_confidence: float = 10.0) -> bool:
        """Check if OCR result contains meaningful text.

        Implements RULE-ERR-008: Determines if text was detected.

        Args:
            result: OCR result to check.
            min_confidence: Minimum confidence threshold.

        Returns:
            True if meaningful text was detected.
        """
        return bool(result.text.strip() and result.confidence >= min_confidence)


async def get_ocr_service() -> OCRService:
    """Get OCR service instance (dependency injection helper).

    Returns:
        OCRService instance.
    """
    return OCRService()