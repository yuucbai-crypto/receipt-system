"""Tests for Receipt Analyzer Orchestration Service."""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.constants import AccountCategory, ReceiptStatus
from app.models.receipt import Receipt
from app.services.ai_analysis_service import AIAnalysisResponse, ReceiptData
from app.services.ocr_service import OCRResult
from app.services.receipt_analyzer import (
    ImageFileManager,
    ReceiptAnalysisResult,
    ReceiptAnalyzer,
    ReceiptAnalyzerConfig,
)


class TestReceiptAnalyzerConfig:
    """Tests for ReceiptAnalyzerConfig."""

    def test_default_config(self, tmp_path: Path) -> None:
        """Test default configuration values."""
        config = ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
        )
        assert config.move_on_failure is True
        assert config.move_on_success is True
        assert config.min_ocr_confidence == 10.0

    def test_custom_config(self, tmp_path: Path) -> None:
        """Test custom configuration values."""
        config = ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
            move_on_failure=False,
            move_on_success=False,
            min_ocr_confidence=20.0,
        )
        assert config.move_on_failure is False
        assert config.move_on_success is False
        assert config.min_ocr_confidence == 20.0


class TestImageFileManager:
    """Tests for ImageFileManager."""

    @pytest.fixture
    def config(self, tmp_path: Path) -> ReceiptAnalyzerConfig:
        """Create test configuration."""
        return ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
        )

    @pytest.fixture
    def file_manager(self, config: ReceiptAnalyzerConfig) -> ImageFileManager:
        """Create file manager instance."""
        return ImageFileManager(config)

    @pytest.fixture
    def sample_image(self, tmp_path: Path) -> Path:
        """Create a sample image file."""
        img_path = tmp_path / "test_receipt.jpg"
        img_path.write_bytes(b"fake image data for testing")
        return img_path

    def test_compute_image_hash(self, file_manager: ImageFileManager, sample_image: Path) -> None:
        """Test SHA-256 hash computation."""
        hash1 = file_manager.compute_image_hash(sample_image)
        hash2 = file_manager.compute_image_hash(sample_image)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_compute_image_hash_different_files(
        self, file_manager: ImageFileManager, tmp_path: Path
    ) -> None:
        """Test different files produce different hashes."""
        file1 = tmp_path / "file1.jpg"
        file2 = tmp_path / "file2.jpg"
        file1.write_bytes(b"data1")
        file2.write_bytes(b"data2")

        hash1 = file_manager.compute_image_hash(file1)
        hash2 = file_manager.compute_image_hash(file2)
        assert hash1 != hash2

    def test_generate_stored_filename(
        self, file_manager: ImageFileManager
    ) -> None:
        """Test filename generation."""
        filename = file_manager.generate_stored_filename(
            original_filename="receipt.jpg",
            receipt_date=datetime(2026, 7, 15),
            store_name="テストスーパー",
            total_amount=1500,
            category=AccountCategory.SUPPLIES,
            tags=["食事", "出張"],
            image_hash="abcdef1234567890",
        )
        assert filename.startswith("20260715_")
        assert "テストスーパー" in filename or "unknown_store" in filename
        assert "1500円" in filename
        assert "消耗品費" in filename
        assert "食事_出張" in filename
        assert "abcdef12" in filename
        assert filename.endswith(".jpg")

    def test_generate_stored_filename_no_date(self, file_manager: ImageFileManager) -> None:
        """Test filename generation without date."""
        filename = file_manager.generate_stored_filename(
            original_filename="receipt.png",
            receipt_date=None,
            store_name="店",
            total_amount=1000,
            category=AccountCategory.ENTERTAINMENT,
            tags=[],
            image_hash="abcdef1234567890",
        )
        # Should use current date
        assert filename.endswith(".png")
        assert "交際費" in filename

    def test_generate_stored_filename_sanitization(self, file_manager: ImageFileManager) -> None:
        """Test filename sanitizes special characters."""
        filename = file_manager.generate_stored_filename(
            original_filename="receipt.jpg",
            receipt_date=datetime(2026, 7, 15),
            store_name='店<>:"/\\|?*名',
            total_amount=1000,
            category=AccountCategory.OTHER,
            tags=["タグ<名"],
            image_hash="abcdef1234567890",
        )
        # Special chars should be replaced
        assert '<' not in filename
        assert '>' not in filename
        assert ':' not in filename
        assert '"' not in filename
        assert '/' not in filename
        assert '\\' not in filename
        assert '|' not in filename
        assert '?' not in filename
        assert '*' not in filename

    def test_move_to_failed(self, file_manager: ImageFileManager, sample_image: Path, tmp_path: Path) -> None:
        """Test moving file to failed directory."""
        dest = file_manager.move_to_failed(sample_image)
        assert dest.exists()
        assert dest.parent == file_manager._config.failed_dir
        assert not sample_image.exists()

    def test_move_to_failed_handles_collision(self, file_manager: ImageFileManager, tmp_path: Path) -> None:
        """Test handling of filename collision in failed directory."""
        # Create existing file in failed dir
        file_manager._config.failed_dir.mkdir(parents=True, exist_ok=True)
        existing = file_manager._config.failed_dir / "test_receipt.jpg"
        existing.write_bytes(b"existing")

        # Create source file
        source = tmp_path / "test_receipt.jpg"
        source.write_bytes(b"source")

        dest = file_manager.move_to_failed(source)
        assert dest.exists()
        assert dest != existing
        assert "failed_" in dest.name

    def test_move_to_unapproved(self, file_manager: ImageFileManager, sample_image: Path) -> None:
        """Test moving file to unapproved directory."""
        dest = file_manager.move_to_unapproved(sample_image, "new_name_20260715_店_1000円_消耗品費_tag_abc12345.jpg")
        assert dest.exists()
        assert dest.parent == file_manager._config.unapproved_dir
        assert dest.name == "new_name_20260715_店_1000円_消耗品費_tag_abc12345.jpg"
        assert not sample_image.exists()

    def test_move_to_unapproved_handles_collision(self, file_manager: ImageFileManager, tmp_path: Path) -> None:
        """Test handling of filename collision in unapproved directory."""
        # Create existing file
        file_manager._config.unapproved_dir.mkdir(parents=True, exist_ok=True)
        existing = file_manager._config.unapproved_dir / "receipt_20260715_店_1000円_消耗品費_tag_abc12345.jpg"
        existing.write_bytes(b"existing")

        source = tmp_path / "receipt.jpg"
        source.write_bytes(b"source")

        dest = file_manager.move_to_unapproved(source, "receipt_20260715_店_1000円_消耗品費_tag_abc12345.jpg")
        assert dest.exists()
        assert dest != existing


class TestReceiptAnalyzer:
    """Tests for ReceiptAnalyzer."""

    @pytest.fixture
    def mock_ocr_service(self) -> MagicMock:
        """Create mock OCR service."""
        service = MagicMock()
        service.extract_text_with_fallback = MagicMock()
        service.has_text = MagicMock()
        return service

    @pytest.fixture
    def mock_ai_service(self) -> AsyncMock:
        """Create mock AI analysis service."""
        service = AsyncMock()
        service.analyze_receipt = AsyncMock()
        service.close = AsyncMock()
        return service

    @pytest.fixture
    def mock_category_classifier(self) -> AsyncMock:
        """Create mock category classifier."""
        classifier = AsyncMock()
        classifier.classify = AsyncMock()
        return classifier

    @pytest.fixture
    def mock_file_manager(self) -> MagicMock:
        """Create mock file manager."""
        manager = MagicMock()
        manager.compute_image_hash = MagicMock(return_value="abcdef1234567890")
        manager.generate_stored_filename = MagicMock(return_value="20260715_店_1000円_消耗品費_tag_abc12345.jpg")
        manager.move_to_unapproved = MagicMock()
        manager.move_to_failed = MagicMock()
        return manager

    @pytest.fixture
    def analyzer(
        self,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        mock_file_manager: MagicMock,
        tmp_path: Path,
    ) -> ReceiptAnalyzer:
        """Create ReceiptAnalyzer with mocked dependencies."""
        config = ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
        )
        return ReceiptAnalyzer(
            config=config,
            ocr_service=mock_ocr_service,
            ai_service=mock_ai_service,
            category_classifier=mock_category_classifier,
            file_manager=mock_file_manager,
        )

    @pytest.fixture
    def sample_image(self, tmp_path: Path) -> Path:
        """Create sample image file."""
        img_path = tmp_path / "receipt.jpg"
        img_path.write_bytes(b"fake image data")
        return img_path

    @pytest.mark.asyncio
    async def test_analyze_receipt_success(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        mock_file_manager: MagicMock,
        sample_image: Path,
    ) -> None:
        """Test successful receipt analysis pipeline."""
        # Setup mocks
        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="店舗名\n合計 1000円",
            confidence=85.0,
            language="jpn+eng",
        )
        mock_ocr_service.has_text.return_value = True

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=True,
            data=ReceiptData(
                receipt_date="2026-07-15",
                store_name="テスト店",
                total_amount=1000,
                tax_amount=100,
                currency="JPY",
                category="消耗品費",
                category_confidence=0.9,
                tags=["食事"],
                ai_comment="昼食代",
                ai_confidence=0.85,
            ),
            error=None,
            model="test-model",
            processing_time_ms=0,
        )

        mock_category_classifier.classify.return_value = (
            AccountCategory.SUPPLIES,
            0.9,
        )

        # Run analysis
        result = await analyzer.analyze_receipt(sample_image)

        # Verify result
        assert result.success is True
        assert result.receipt is not None
        assert result.ocr_result is not None
        assert result.ai_response is not None
        assert result.category == AccountCategory.SUPPLIES
        assert result.category_confidence == 0.9
        assert result.error is None
        assert result.processing_time_ms > 0

        # Verify receipt model
        receipt = result.receipt
        assert isinstance(receipt, Receipt)
        assert receipt.store_name == "テスト店"
        assert receipt.total_amount == 1000
        assert receipt.tax_amount == 100
        assert receipt.category_confidence == 0.9
        assert receipt.ai_comment == "昼食代"
        assert receipt.ai_confidence == 0.85
        assert receipt.status == ReceiptStatus.UNAPPROVED

        # Verify file manager called
        mock_file_manager.move_to_unapproved.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_receipt_ai_failure_moves_to_failed(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_file_manager: MagicMock,
        sample_image: Path,
    ) -> None:
        """Test AI failure after retries moves file to failed."""
        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="text", confidence=80.0, language="jpn+eng"
        )
        mock_ocr_service.has_text.return_value = True

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=False,
            data=None,
            error="API timeout after 3 retries",
            model="test-model",
            processing_time_ms=5000,
        )

        result = await analyzer.analyze_receipt(sample_image)

        assert result.success is False
        assert "API timeout" in result.error
        assert result.receipt is None
        mock_file_manager.move_to_failed.assert_called_once_with(sample_image)

    @pytest.mark.asyncio
    async def test_analyze_receipt_low_ocr_confidence_continues(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        sample_image: Path,
    ) -> None:
        """Test low OCR confidence continues pipeline but marks result."""
        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="", confidence=5.0, language="jpn+eng"
        )
        mock_ocr_service.has_text.return_value = False  # Below threshold

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=True,
            data=ReceiptData(
                store_name="店",
                total_amount=500,
                category="その他",
                category_confidence=0.3,
                tags=[],
                ai_comment="OCR信頼度低",
                ai_confidence=0.4,
            ),
            error=None,
            model="test-model",
            processing_time_ms=0,
        )

        mock_category_classifier.classify.return_value = (
            AccountCategory.OTHER,
            0.3,
        )

        result = await analyzer.analyze_receipt(sample_image)

        # Should still succeed (AI might work with image context)
        assert result.success is True
        assert result.ocr_result.confidence == 5.0

    @pytest.mark.asyncio
    async def test_analyze_receipt_ocr_failure_fallback(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        mock_file_manager: MagicMock,
        sample_image: Path,
    ) -> None:
        """Test OCR complete failure returns empty result."""
        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="", confidence=0.0, language="jpn+eng"
        )
        mock_ocr_service.has_text.return_value = False

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=False,
            data=None,
            error="OCR text is empty",
            model="test-model",
            processing_time_ms=0,
        )

        result = await analyzer.analyze_receipt(sample_image)

        assert result.success is False
        assert "empty" in result.error.lower()
        mock_file_manager.move_to_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_receipt_exception_handling(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_file_manager: MagicMock,
        sample_image: Path,
    ) -> None:
        """Test unexpected exception handling."""
        mock_ocr_service.extract_text_with_fallback.side_effect = RuntimeError("Unexpected error")

        result = await analyzer.analyze_receipt(sample_image)

        assert result.success is False
        assert "Unexpected error" in result.error
        mock_file_manager.move_to_failed.assert_called_once_with(sample_image)

    @pytest.mark.asyncio
    async def test_analyze_receipt_no_move_on_failure(
        self,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_file_manager: MagicMock,
        tmp_path: Path,
        sample_image: Path,
    ) -> None:
        """Test file not moved when move_on_failure is False."""
        config = ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
            move_on_failure=False,
        )
        analyzer = ReceiptAnalyzer(
            ocr_service=mock_ocr_service,
            ai_service=mock_ai_service,
            category_classifier=None,
            config=config,
            file_manager=mock_file_manager,
        )

        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="text", confidence=80.0, language="jpn+eng"
        )
        mock_ocr_service.has_text.return_value = True

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=False,
            data=None,
            error="AI failed",
            model="test-model",
            processing_time_ms=0,
        )

        await analyzer.analyze_receipt(sample_image)

        mock_file_manager.move_to_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_receipt_no_move_on_success(
        self,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        mock_file_manager: MagicMock,
        tmp_path: Path,
        sample_image: Path,
    ) -> None:
        """Test file not moved when move_on_success is False."""
        config = ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
            move_on_success=False,
        )
        analyzer = ReceiptAnalyzer(
            ocr_service=mock_ocr_service,
            ai_service=mock_ai_service,
            category_classifier=mock_category_classifier,
            config=config,
            file_manager=mock_file_manager,
        )

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=True,
            data=ReceiptData(
                store_name="店",
                total_amount=1000,
                category="消耗品費",
                category_confidence=0.9,
                tags=[],
                ai_comment="comment",
                ai_confidence=0.8,
            ),
            error=None,
            model="test-model",
            processing_time_ms=0,
        )

        mock_category_classifier.classify.return_value = (
            AccountCategory.SUPPLIES,
            0.9,
        )

        await analyzer.analyze_receipt(sample_image)

        mock_file_manager.move_to_unapproved.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_receipt_date_parsing(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        sample_image: Path,
    ) -> None:
        """Test receipt date parsing from ISO format."""
        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="text", confidence=80.0, language="jpn+eng"
        )
        mock_ocr_service.has_text.return_value = True

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=True,
            data=ReceiptData(
                receipt_date="2026-07-15T12:30:00",
                store_name="店",
                total_amount=1000,
                category="消耗品費",
                category_confidence=0.9,
                tags=[],
                ai_comment="",
                ai_confidence=0.8,
            ),
            error=None,
            model="test-model",
            processing_time_ms=0,
        )

        mock_category_classifier.classify.return_value = (
            AccountCategory.SUPPLIES,
            0.9,
        )

        result = await analyzer.analyze_receipt(sample_image)

        assert result.success is True
        assert result.receipt.receipt_date == datetime(2026, 7, 15, 12, 30)

    @pytest.mark.asyncio
    async def test_analyze_receipt_invalid_date(
        self,
        analyzer: ReceiptAnalyzer,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        sample_image: Path,
    ) -> None:
        """Test invalid date format doesn't break pipeline."""
        mock_ocr_service.extract_text_with_fallback.return_value = OCRResult(
            text="text", confidence=80.0, language="jpn+eng"
        )
        mock_ocr_service.has_text.return_value = True

        mock_ai_service.analyze_receipt.return_value = AIAnalysisResponse(
            success=True,
            data=ReceiptData(
                receipt_date="invalid-date",
                store_name="店",
                total_amount=1000,
                category="消耗品費",
                category_confidence=0.9,
                tags=[],
                ai_comment="",
                ai_confidence=0.8,
            ),
            error=None,
            model="test-model",
            processing_time_ms=0,
        )

        mock_category_classifier.classify.return_value = (
            AccountCategory.SUPPLIES,
            0.9,
        )

        result = await analyzer.analyze_receipt(sample_image)

        assert result.success is True
        assert result.receipt.receipt_date is None  # Invalid date becomes None

    @pytest.mark.asyncio
    async def test_close(self, analyzer: ReceiptAnalyzer, mock_ai_service: AsyncMock) -> None:
        """Test closing analyzer closes AI service."""
        await analyzer.close()
        mock_ai_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(
        self,
        mock_ocr_service: MagicMock,
        mock_ai_service: AsyncMock,
        mock_category_classifier: AsyncMock,
        mock_file_manager: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test async context manager."""
        config = ReceiptAnalyzerConfig(
            unparsed_dir=tmp_path / "unparsed",
            unapproved_dir=tmp_path / "unapproved",
            failed_dir=tmp_path / "failed",
            approved_dir=tmp_path / "approved",
        )
        async with ReceiptAnalyzer(
            config=config,
            ocr_service=mock_ocr_service,
            ai_service=mock_ai_service,
            category_classifier=mock_category_classifier,
            file_manager=mock_file_manager,
        ) as analyzer:
            assert isinstance(analyzer, ReceiptAnalyzer)

        mock_ai_service.close.assert_called_once()


class TestGetReceiptAnalyzer:
    """Tests for get_receipt_analyzer dependency injection helper."""

    @pytest.mark.asyncio
    async def test_get_receipt_analyzer(self) -> None:
        """Test get_receipt_analyzer returns ReceiptAnalyzer instance."""
        from app.services.receipt_analyzer import get_receipt_analyzer

        analyzer = await get_receipt_analyzer()
        assert isinstance(analyzer, ReceiptAnalyzer)
        await analyzer.close()


class TestReceiptAnalysisResult:
    """Tests for ReceiptAnalysisResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result creation."""
        receipt = Receipt(
            original_filename="test.jpg",
            stored_filename="test.jpg",
            file_path="/path/test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
        )
        ocr_result = OCRResult(text="text", confidence=90.0, language="jpn+eng")
        ai_response = AIAnalysisResponse(
            success=True,
            data=ReceiptData(store_name="店"),
            error=None,
            model="model",
            processing_time_ms=1000,
        )

        result = ReceiptAnalysisResult(
            success=True,
            receipt=receipt,
            ocr_result=ocr_result,
            ai_response=ai_response,
            category=AccountCategory.SUPPLIES,
            category_confidence=0.9,
            processing_time_ms=1500,
        )

        assert result.success is True
        assert result.receipt is receipt
        assert result.ocr_result is ocr_result
        assert result.ai_response is ai_response
        assert result.category == AccountCategory.SUPPLIES
        assert result.category_confidence == 0.9
        assert result.error is None
        assert result.processing_time_ms == 1500

    def test_failure_result(self) -> None:
        """Test failure result creation."""
        result = ReceiptAnalysisResult(
            success=False,
            error="Processing failed",
            processing_time_ms=100,
        )

        assert result.success is False
        assert result.receipt is None
        assert result.ocr_result is None
        assert result.ai_response is None
        assert result.category is None
        assert result.category_confidence == 0.0
        assert result.error == "Processing failed"
        assert result.processing_time_ms == 100