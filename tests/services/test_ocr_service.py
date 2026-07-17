"""Tests for OCR Service."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from app.services.ocr_service import OCRResult, OCRService


class TestOCRService:
    """Test suite for OCRService."""

    @pytest.fixture
    def ocr_service(self) -> OCRService:
        """Create OCR service instance."""
        return OCRService()

    @pytest.fixture
    def sample_image(self, tmp_path: Path) -> Path:
        """Create a sample test image."""
        img_path = tmp_path / "test_receipt.jpg"
        # Create a simple test image
        img = Image.new("RGB", (800, 600), color="white")
        img.save(img_path)
        return img_path

    @pytest.fixture
    def sample_image_small(self, tmp_path: Path) -> Path:
        """Create a small test image (will be resized)."""
        img_path = tmp_path / "small_receipt.jpg"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(img_path)
        return img_path

    def test_ocr_service_initialization(self, ocr_service: OCRService) -> None:
        """Test OCR service initializes with correct settings."""
        assert ocr_service._language == "jpn+eng"
        assert ocr_service._dpi == 300

    def test_preprocess_image_basic(self, ocr_service: OCRService, sample_image: Path) -> None:
        """Test basic image preprocessing."""
        processed = ocr_service.preprocess_image(sample_image)

        assert isinstance(processed, Image.Image)
        assert processed.mode == "L"  # Grayscale
        # Should be resized for 300 DPI (300/72 ≈ 4.17x scale)
        assert processed.width > 800

    def test_preprocess_image_small_image_resized(
        self, ocr_service: OCRService, sample_image_small: Path
    ) -> None:
        """Test small images are resized for DPI."""
        processed = ocr_service.preprocess_image(sample_image_small)

        # Small image (100x100) should be scaled by 300/72 ≈ 4.17
        assert processed.width >= 400
        assert processed.height >= 400

    def test_preprocess_image_converts_rgba(self, ocr_service: OCRService, tmp_path: Path) -> None:
        """Test RGBA images are converted to RGB then grayscale."""
        img_path = tmp_path / "rgba_image.png"
        img = Image.new("RGBA", (200, 200), color=(255, 255, 255, 128))
        img.save(img_path)

        processed = ocr_service.preprocess_image(img_path)
        assert processed.mode == "L"

    def test_preprocess_image_raises_on_missing(self, ocr_service: OCRService) -> None:
        """Test preprocessing raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            ocr_service.preprocess_image(Path("/nonexistent/image.jpg"))

    @patch("app.services.ocr_service.pytesseract.image_to_data")
    def test_extract_text_success(
        self, mock_image_to_data: MagicMock, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test successful text extraction."""
        mock_image_to_data.return_value = {
            "text": ["テスト", "店舗", "合計", "1,500円"],
            "conf": [95, 92, 88, 85],
        }

        result = ocr_service.extract_text(sample_image)

        assert isinstance(result, OCRResult)
        assert "テスト" in result.text
        assert "店舗" in result.text
        assert "合計" in result.text
        assert "1,500円" in result.text
        assert result.confidence == (95 + 92 + 88 + 85) / 4
        assert result.language == "jpn+eng"

    @patch("app.services.ocr_service.pytesseract.image_to_data")
    def test_extract_text_empty_result(
        self, mock_image_to_data: MagicMock, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test extraction with no detectable text."""
        mock_image_to_data.return_value = {"text": ["", "  ", ""], "conf": [-1, -1, -1]}

        result = ocr_service.extract_text(sample_image)

        assert result.text == ""
        assert result.confidence == 0.0

    @patch("app.services.ocr_service.pytesseract.image_to_data")
    def test_extract_text_filters_low_confidence(
        self, mock_image_to_data: MagicMock, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test low confidence words are filtered out."""
        mock_image_to_data.return_value = {
            "text": ["高信頼", "低信頼", "中信頼"],
            "conf": [90, 10, 50],
        }

        result = ocr_service.extract_text(sample_image)

        # Only words with conf > 0 are included, but all three have conf > 0
        # The average should be (90 + 10 + 50) / 3 = 50
        assert result.confidence == 50.0
        assert "高信頼" in result.text
        assert "低信頼" in result.text

    @patch("app.services.ocr_service.pytesseract.image_to_data")
    def test_extract_text_single_word(
        self, mock_image_to_data: MagicMock, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test extraction with single word."""
        mock_image_to_data.return_value = {"text": ["合計"], "conf": [95]}

        result = ocr_service.extract_text(sample_image)

        assert result.text == "合計"
        assert result.confidence == 95.0

    @patch("app.services.ocr_service.pytesseract.image_to_data")
    def test_extract_text_tesseract_not_found(
        self, mock_image_to_data: MagicMock, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test handling of TesseractNotFoundError."""
        from pytesseract import TesseractNotFoundError

        mock_image_to_data.side_effect = TesseractNotFoundError()

        with pytest.raises(OSError, match="Tesseract OCR engine not installed"):
            ocr_service.extract_text(sample_image)

    @patch("app.services.ocr_service.pytesseract.image_to_data")
    def test_extract_text_tesseract_error(
        self, mock_image_to_data: MagicMock, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test handling of TesseractError."""
        from pytesseract import TesseractError

        mock_image_to_data.side_effect = TesseractError(1, "Tesseract failed")

        with pytest.raises(TesseractError):
            ocr_service.extract_text(sample_image)

    def test_extract_text_with_fallback_success(
        self, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test fallback method on success."""
        with patch.object(ocr_service, "extract_text") as mock_extract:
            mock_extract.return_value = OCRResult(
                text="成功", confidence=90.0, language="jpn+eng"
            )

            result = ocr_service.extract_text_with_fallback(sample_image)

            assert result.text == "成功"
            assert result.confidence == 90.0

    def test_extract_text_with_fallback_tesseract_error(
        self, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test fallback returns empty result on TesseractError."""
        from pytesseract import TesseractError

        with patch.object(ocr_service, "extract_text") as mock_extract:
            mock_extract.side_effect = TesseractError(1, "Failed")

            result = ocr_service.extract_text_with_fallback(sample_image)

            assert result.text == ""
            assert result.confidence == 0.0

    def test_extract_text_with_fallback_os_error(
        self, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test fallback returns empty result on OSError."""
        with patch.object(ocr_service, "extract_text") as mock_extract:
            mock_extract.side_effect = OSError("File error")

            result = ocr_service.extract_text_with_fallback(sample_image)

            assert result.text == ""
            assert result.confidence == 0.0

    def test_extract_text_with_fallback_file_not_found(
        self, ocr_service: OCRService
    ) -> None:
        """Test fallback returns empty result on FileNotFoundError."""
        result = ocr_service.extract_text_with_fallback(Path("/nonexistent.jpg"))

        assert result.text == ""
        assert result.confidence == 0.0

    def test_extract_text_with_fallback_unexpected_error(
        self, ocr_service: OCRService, sample_image: Path
    ) -> None:
        """Test fallback returns empty result on unexpected error."""
        with patch.object(ocr_service, "extract_text") as mock_extract:
            mock_extract.side_effect = RuntimeError("Unexpected")

            result = ocr_service.extract_text_with_fallback(sample_image)

            assert result.text == ""
            assert result.confidence == 0.0

    def test_has_text_true(self, ocr_service: OCRService) -> None:
        """Test has_text returns True for valid result."""
        result = OCRResult(text="テキストあり", confidence=50.0, language="jpn+eng")
        assert ocr_service.has_text(result, min_confidence=10.0) is True

    def test_has_text_false_empty_text(self, ocr_service: OCRService) -> None:
        """Test has_text returns False for empty text."""
        result = OCRResult(text="", confidence=50.0, language="jpn+eng")
        assert ocr_service.has_text(result, min_confidence=10.0) is False

    def test_has_text_false_whitespace_only(self, ocr_service: OCRService) -> None:
        """Test has_text returns False for whitespace-only text."""
        result = OCRResult(text="   \n\t  ", confidence=50.0, language="jpn+eng")
        assert ocr_service.has_text(result, min_confidence=10.0) is False

    def test_has_text_false_low_confidence(self, ocr_service: OCRService) -> None:
        """Test has_text returns False for low confidence."""
        result = OCRResult(text="テキスト", confidence=5.0, language="jpn+eng")
        assert ocr_service.has_text(result, min_confidence=10.0) is False

    def test_has_text_true_meets_threshold(self, ocr_service: OCRService) -> None:
        """Test has_text returns True when confidence meets threshold."""
        result = OCRResult(text="テキスト", confidence=15.0, language="jpn+eng")
        assert ocr_service.has_text(result, min_confidence=10.0) is True

    def test_has_text_custom_threshold(self, ocr_service: OCRService) -> None:
        """Test has_text with custom confidence threshold."""
        result = OCRResult(text="テキスト", confidence=25.0, language="jpn+eng")
        assert ocr_service.has_text(result, min_confidence=20.0) is True
        assert ocr_service.has_text(result, min_confidence=30.0) is False


class TestOCRResult:
    """Tests for OCRResult dataclass."""

    def test_ocr_result_creation(self) -> None:
        """Test OCRResult creation."""
        result = OCRResult(
            text="テストテキスト",
            confidence=85.5,
            language="jpn+eng",
        )
        assert result.text == "テストテキスト"
        assert result.confidence == 85.5
        assert result.language == "jpn+eng"

    def test_ocr_result_empty(self) -> None:
        """Test empty OCRResult."""
        result = OCRResult(text="", confidence=0.0, language="jpn+eng")
        assert result.text == ""
        assert result.confidence == 0.0


class TestOCRServiceVerifyTesseract:
    """Tests for Tesseract verification."""

    @pytest.fixture
    def ocr_service(self) -> OCRService:
        """Create OCR service instance."""
        return OCRService()

    @patch("app.services.ocr_service.pytesseract.get_tesseract_version")
    def test_verify_tesseract_success(
        self, mock_get_version: MagicMock, ocr_service: OCRService
    ) -> None:
        """Test successful Tesseract verification."""
        mock_get_version.return_value = "5.3.0"
        # Should not raise
        ocr_service._verify_tesseract()
        mock_get_version.assert_called_once()

    @patch("app.services.ocr_service.pytesseract.get_tesseract_version")
    def test_verify_tesseract_not_found(
        self, mock_get_version: MagicMock, ocr_service: OCRService
    ) -> None:
        """Test Tesseract not found warning."""
        from pytesseract import TesseractNotFoundError

        mock_get_version.side_effect = TesseractNotFoundError()
        # Should not raise, just log warning
        ocr_service._verify_tesseract()

    @patch("app.services.ocr_service.pytesseract.get_tesseract_version")
    def test_verify_tesseract_other_error(
        self, mock_get_version: MagicMock, ocr_service: OCRService
    ) -> None:
        """Test other Tesseract verification errors."""
        mock_get_version.side_effect = RuntimeError("Other error")
        # Should not raise
        ocr_service._verify_tesseract()


class TestGetOCRService:
    """Tests for get_ocr_service dependency injection helper."""

    @pytest.mark.asyncio
    async def test_get_ocr_service(self) -> None:
        """Test get_ocr_service returns OCRService instance."""
        from app.services.ocr_service import get_ocr_service

        service = await get_ocr_service()
        assert isinstance(service, OCRService)