"""Tests for File Sorting Service."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.constants import AccountCategory, ReceiptStatus
from app.models.receipt import Receipt
from app.services.file_sorting_service import (
    FileSortingService,
    get_file_sorting_service,
    FileSortResult,
)


class TestFileSortingService:
    """Tests for FileSortingService."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create file sorting service with temp directories."""
        with patch("app.core.config._settings") as mock_settings:
            mock_settings.approved_dir = tmp_path / "approved"
            mock_settings.supported_image_extensions = [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]
            service = FileSortingService()
            return service

    @pytest.fixture
    def approved_receipt(self):
        """Create an approved receipt."""
        return Receipt(
            id=1,
            original_filename="receipt_20260715.jpg",
            stored_filename="receipt_20260715.jpg",
            file_path="/tmp/receipt_20260715.jpg",
            file_size=100000,
            mime_type="image/jpeg",
            image_hash="abcdef1234567890",
            ocr_text="店舗名\n合計 1000円",
            ocr_confidence=90.0,
            receipt_date=datetime(2026, 7, 15, 12, 30),
            store_name="テストスーパー",
            total_amount=1000,
            tax_amount=100,
            currency="JPY",
            category_id=1,
            category_confidence=0.95,
            ai_comment="日用品購入",
            ai_confidence=0.9,
            status=ReceiptStatus.APPROVED,
        )

    def test_generate_approved_filename_basic(self, service, approved_receipt):
        """Test basic filename generation."""
        filename = service.generate_approved_filename(approved_receipt)

        assert filename.startswith("2026-07-15_")
        assert "テストスーパー" in filename
        assert "1000円" in filename
        assert filename.endswith(".jpg")

    def test_generate_approved_filename_format(self, service, approved_receipt):
        """Test filename format matches YYYY-MM-DD_店舗名_金額円.jpg."""
        filename = service.generate_approved_filename(approved_receipt)

        # Check format: YYYY-MM-DD_店舗名_金額円.jpg
        parts = filename.split("_")
        assert len(parts) >= 3
        assert parts[0] == "2026-07-15"
        assert parts[1] == "テストスーパー"
        assert parts[2] == "1000円.jpg"

    def test_generate_approved_filename_no_date(self, service):
        """Test filename generation without receipt date."""
        receipt = Receipt(
            id=1,
            original_filename="receipt.jpg",
            stored_filename="receipt.jpg",
            file_path="/tmp/receipt.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abcdef1234567890",
            store_name="店舗",
            total_amount=500,
            status=ReceiptStatus.APPROVED,
        )

        filename = service.generate_approved_filename(receipt)

        # Should use current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        assert filename.startswith(current_date + "_")
        assert "店舗" in filename
        assert "500円" in filename

    def test_generate_approved_filename_no_store_name(self, service):
        """Test filename generation without store name."""
        receipt = Receipt(
            id=1,
            original_filename="receipt.jpg",
            stored_filename="receipt.jpg",
            file_path="/tmp/receipt.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abcdef1234567890",
            total_amount=500,
            receipt_date=datetime(2026, 7, 15),
            status=ReceiptStatus.APPROVED,
        )

        filename = service.generate_approved_filename(receipt)

        assert "不明店舗" in filename

    def test_generate_approved_filename_sanitization(self, service):
        """Test filename sanitization for special characters."""
        receipt = Receipt(
            id=1,
            original_filename="receipt.jpg",
            stored_filename="receipt.jpg",
            file_path="/tmp/receipt.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abcdef1234567890",
            store_name='店<>:"/\\|?*名',
            total_amount=1000,
            receipt_date=datetime(2026, 7, 15),
            status=ReceiptStatus.APPROVED,
        )

        filename = service.generate_approved_filename(receipt)

        # Special characters should be replaced
        assert "<" not in filename
        assert ">" not in filename
        assert ":" not in filename
        assert '"' not in filename
        assert "/" not in filename
        assert "\\" not in filename
        assert "|" not in filename
        assert "?" not in filename
        assert "*" not in filename

    def test_get_category_folder(self, service, approved_receipt):
        """Test category folder name generation."""
        folder = service._get_category_folder(approved_receipt)
        assert folder == "category_1"

    def test_get_category_folder_none(self, service):
        """Test category folder with no category."""
        receipt = Receipt(
            id=1,
            original_filename="receipt.jpg",
            stored_filename="receipt.jpg",
            file_path="/tmp/receipt.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abcdef1234567890",
            status=ReceiptStatus.APPROVED,
        )

        folder = service._get_category_folder(receipt)
        assert folder == AccountCategory.OTHER.value

    def test_get_year_month_folder(self, service, approved_receipt):
        """Test year-month folder name."""
        folder = service._get_year_month_folder(approved_receipt)
        assert folder == "2026-07"

    def test_get_year_month_folder_none(self, service):
        """Test year-month folder with no date."""
        receipt = Receipt(
            id=1,
            original_filename="receipt.jpg",
            stored_filename="receipt.jpg",
            file_path="/tmp/receipt.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abcdef1234567890",
            status=ReceiptStatus.APPROVED,
        )

        folder = service._get_year_month_folder(receipt)
        assert folder == datetime.now().strftime("%Y-%m")

    def test_build_destination_path(self, service, approved_receipt):
        """Test destination path building."""
        filename = "2026-07-15_テストスーパー_1000円.jpg"
        path = service._build_destination_path(approved_receipt, filename)

        assert path.name == filename
        assert "category_1" in str(path)
        assert "2026-07" in str(path)

    @patch("shutil.move")
    def test_sort_approved_receipt_success(self, mock_move, service, approved_receipt, tmp_path):
        """Test successful file sorting."""
        # Create source file
        source = tmp_path / "receipt_20260715.jpg"
        source.write_bytes(b"fake image data")

        approved_receipt.file_path = str(source)
        approved_receipt.original_filename = "receipt_20260715.jpg"

        result = service.sort_approved_receipt(approved_receipt)

        assert result.success is True
        assert result.new_filename is not None
        assert result.destination_path is not None
        assert "category_1" in str(result.destination_path)
        assert "2026-07" in str(result.destination_path)
        mock_move.assert_called_once()

    def test_sort_approved_receipt_source_not_found(self, service, approved_receipt):
        """Test file sorting with missing source file."""
        approved_receipt.file_path = "/nonexistent/receipt.jpg"

        result = service.sort_approved_receipt(approved_receipt)

        assert result.success is False
        assert "not found" in result.error

    @patch("shutil.move")
    def test_sort_approved_receipt_collision(self, mock_move, service, approved_receipt, tmp_path):
        """Test file sorting with name collision."""
        source = tmp_path / "receipt_20260715.jpg"
        source.write_bytes(b"fake image data")

        # Create existing file at destination
        dest_dir = service._config.approved_dir / "category_1" / "2026-07"
        dest_dir.mkdir(parents=True, exist_ok=True)
        existing = dest_dir / "2026-07-15_テストスーパー_1000円.jpg"
        existing.write_bytes(b"existing")

        approved_receipt.file_path = str(source)
        approved_receipt.original_filename = "receipt_20260715.jpg"

        result = service.sort_approved_receipt(approved_receipt)

        assert result.success is True
        # Should have counter suffix
        assert "_1" in result.new_filename or "_2" in result.new_filename

    def test_get_approved_file_path(self, service, approved_receipt):
        """Test getting expected approved file path."""
        path = service.get_approved_file_path(approved_receipt)

        assert path.name.startswith("2026-07-15_")
        assert "テストスーパー" in path.name
        assert "1000円" in path.name

    def test_list_approved_files(self, service, tmp_path):
        """Test listing approved files."""
        # Create test files
        cat_dir = service._config.approved_dir / "category_1" / "2026-07"
        cat_dir.mkdir(parents=True, exist_ok=True)

        file1 = cat_dir / "2026-07-15_店A_1000円.jpg"
        file1.write_bytes(b"file1")

        file2 = cat_dir / "2026-07-16_店B_2000円.jpg"
        file2.write_bytes(b"file2")

        files = service.list_approved_files(category="category_1", year_month="2026-07")

        assert len(files) == 2
        assert file1 in files
        assert file2 in files

    def test_list_approved_files_filter_category(self, service, tmp_path):
        """Test listing approved files with category filter."""
        cat1_dir = service._config.approved_dir / "category_1" / "2026-07"
        cat1_dir.mkdir(parents=True, exist_ok=True)
        file1 = cat1_dir / "2026-07-15_店A_1000円.jpg"
        file1.write_bytes(b"file1")

        cat2_dir = service._config.approved_dir / "category_2" / "2026-07"
        cat2_dir.mkdir(parents=True, exist_ok=True)
        file2 = cat2_dir / "2026-07-15_店B_2000円.jpg"
        file2.write_bytes(b"file2")

        files = service.list_approved_files(category="category_1")

        assert len(files) == 1
        assert file1 in files
        assert file2 not in files

    def test_list_approved_files_filter_year_month(self, service, tmp_path):
        """Test listing approved files with year-month filter."""
        jul_dir = service._config.approved_dir / "category_1" / "2026-07"
        jul_dir.mkdir(parents=True, exist_ok=True)
        file1 = jul_dir / "2026-07-15_店A_1000円.jpg"
        file1.write_bytes(b"file1")

        aug_dir = service._config.approved_dir / "category_1" / "2026-08"
        aug_dir.mkdir(parents=True, exist_ok=True)
        file2 = aug_dir / "2026-08-15_店B_2000円.jpg"
        file2.write_bytes(b"file2")

        files = service.list_approved_files(category="category_1", year_month="2026-07")

        assert len(files) == 1
        assert file1 in files
        assert file2 not in files


class TestFileSortResult:
    """Tests for FileSortResult dataclass."""

    def test_success_result(self, tmp_path):
        """Test successful sort result."""
        src = tmp_path / "source.jpg"
        dest = tmp_path / "dest.jpg"

        result = FileSortResult(
            success=True,
            source_path=src,
            destination_path=dest,
            new_filename="dest.jpg",
            category_folder="category_1",
            year_month_folder="2026-07",
        )

        assert result.success is True
        assert result.destination_path == dest
        assert result.error is None

    def test_failure_result(self, tmp_path):
        """Test failed sort result."""
        src = tmp_path / "source.jpg"

        result = FileSortResult(
            success=False,
            source_path=src,
            error="File not found",
        )

        assert result.success is False
        assert result.error == "File not found"


class TestGetFileSortingService:
    """Tests for get_file_sorting_service helper."""

    def test_returns_instance(self):
        """Test that helper returns service instance."""
        service = get_file_sorting_service()
        assert isinstance(service, FileSortingService)