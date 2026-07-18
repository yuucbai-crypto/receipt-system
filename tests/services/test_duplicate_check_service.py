"""Tests for DuplicateCheckService."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.core.constants import ReceiptStatus
from app.models.receipt import Receipt
from app.services.duplicate_check_service import (
    DEFAULT_DUPLICATE_THRESHOLD,
    DEFAULT_WEIGHTS,
    DuplicateCheckService,
    DuplicateScoreComponents,
    DuplicateCheckResult,
    MIN_REQUIRED_FIELDS,
)


class TestDuplicateCheckService:
    """Tests for DuplicateCheckService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance with mock session."""
        return DuplicateCheckService(mock_session)

    @pytest.fixture
    def source_receipt(self):
        """Create source receipt for testing."""
        return Receipt(
            id=1,
            original_filename="test1.jpg",
            stored_filename="test1.jpg",
            file_path="/path/test1.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
            ocr_text="店舗A\n合計 1000円",
            ocr_confidence=90.0,
            receipt_date=datetime(2026, 7, 15, 12, 0),
            store_name="店舗A",
            total_amount=1000,
            tax_amount=100,
            currency="JPY",
            category_id=1,
            category_confidence=0.9,
            status=ReceiptStatus.UNAPPROVED,
        )

    @pytest.fixture
    def target_receipt(self):
        """Create target receipt for testing."""
        return Receipt(
            id=2,
            original_filename="test2.jpg",
            stored_filename="test2.jpg",
            file_path="/path/test2.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
            ocr_text="店舗A\n合計 1000円",
            ocr_confidence=85.0,
            receipt_date=datetime(2026, 7, 15, 13, 0),
            store_name="店舗A",
            total_amount=1000,
            tax_amount=100,
            currency="JPY",
            category_id=1,
            category_confidence=0.85,
            status=ReceiptStatus.APPROVED,
        )

    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to 1.0."""
        total = sum(DEFAULT_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_weights_normalization(self, mock_session):
        """Test that custom weights are normalized."""
        custom_weights = {"store_name": 0.5, "amount": 0.5}
        service = DuplicateCheckService(mock_session, weights=custom_weights)
        total = sum(service._weights.values())
        assert abs(total - 1.0) < 0.001

    def test_compute_store_name_score_exact_match(self, service):
        """Test store name score for exact match."""
        score = service._compute_store_name_score("店舗A", "店舗A")
        assert score == 1.0

    def test_compute_store_name_score_partial_match(self, service):
        """Test store name score for partial match."""
        score = service._compute_store_name_score("店舗A", "店舗B")
        assert score is not None
        assert 0.0 < score < 1.0

    def test_compute_store_name_score_none(self, service):
        """Test store name score with None input."""
        score = service._compute_store_name_score(None, "店舗A")
        assert score is None

    def test_compute_amount_score_exact(self, service):
        """Test amount score for exact match."""
        score = service._compute_amount_score(1000, 1000)
        assert score == 1.0

    def test_compute_amount_score_close(self, service):
        """Test amount score for close amounts."""
        score = service._compute_amount_score(1000, 950)
        assert score is not None
        assert 0.9 < score < 1.0

    def test_compute_amount_score_none(self, service):
        """Test amount score with None input."""
        score = service._compute_amount_score(None, 1000)
        assert score is None

    def test_compute_date_score_same_day(self, service):
        """Test date score for same day."""
        d1 = datetime(2026, 7, 15, 12, 0)
        d2 = datetime(2026, 7, 15, 13, 0)
        score = service._compute_date_score(d1, d2)
        assert score == 1.0

    def test_compute_date_score_one_day_diff(self, service):
        """Test date score for 1 day difference."""
        d1 = datetime(2026, 7, 15)
        d2 = datetime(2026, 7, 16)
        score = service._compute_date_score(d1, d2)
        assert score == 0.9

    def test_compute_date_score_seven_days(self, service):
        """Test date score for 7 days difference."""
        d1 = datetime(2026, 7, 15)
        d2 = datetime(2026, 7, 22)
        score = service._compute_date_score(d1, d2)
        assert score == 0.5

    def test_compute_metadata_score(self, service, source_receipt, target_receipt):
        """Test metadata score computation."""
        score = service._compute_metadata_score(source_receipt, target_receipt)
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_compute_image_hash_score_exact(self, service):
        """Test image hash score for exact match."""
        hash_val = "a" * 64
        score = service._compute_image_hash_score(hash_val, hash_val)
        assert score == 1.0

    def test_compute_image_hash_score_different(self, service):
        """Test image hash score for different hashes."""
        # Different SHA-256 hashes should have Hamming distance
        score = service._compute_image_hash_score("a" * 64, "b" * 64)
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_compute_ocr_similarity_score(self, service):
        """Test OCR similarity score."""
        score = service._compute_ocr_similarity_score("テスト", "テスト")
        assert score == 1.0

    def test_check_sufficient_data_true(self, service):
        """Test sufficient data check with enough fields."""
        components = DuplicateScoreComponents(
            store_name_score=0.9,
            amount_score=1.0,
            date_score=1.0,
            metadata_score=0.8,
            image_hash_score=1.0,
            ocr_similarity_score=0.9,
            composite_score=0.0,
            has_sufficient_data=False,
        )
        assert service._check_sufficient_data(components) is True

    def test_check_sufficient_data_false(self, service):
        """Test sufficient data check with insufficient fields."""
        components = DuplicateScoreComponents(
            store_name_score=None,
            amount_score=None,
            date_score=1.0,
            metadata_score=None,
            image_hash_score=None,
            ocr_similarity_score=None,
            composite_score=0.0,
            has_sufficient_data=False,
        )
        assert service._check_sufficient_data(components) is False

    def test_compute_composite_score(self, service):
        """Test composite score computation."""
        components = DuplicateScoreComponents(
            store_name_score=1.0,
            amount_score=1.0,
            date_score=1.0,
            metadata_score=1.0,
            image_hash_score=1.0,
            ocr_similarity_score=1.0,
            composite_score=0.0,
            has_sufficient_data=True,
        )
        score = service._compute_composite_score(components)
        assert abs(score - 1.0) < 0.01

    def test_compute_composite_score_partial(self, service):
        """Test composite score with partial components."""
        components = DuplicateScoreComponents(
            store_name_score=1.0,
            amount_score=1.0,
            date_score=None,
            metadata_score=None,
            image_hash_score=None,
            ocr_similarity_score=None,
            composite_score=0.0,
            has_sufficient_data=True,
        )
        score = service._compute_composite_score(components)
        # With only store_name (0.25) and amount (0.20) weights
        # Normalized: 0.25/(0.25+0.20) = 0.556 for store_name
        #             0.20/(0.25+0.20) = 0.444 for amount
        expected = (1.0 * 0.25 + 1.0 * 0.20) / (0.25 + 0.20)
        assert abs(score - expected) < 0.01

    def test_is_duplicate_threshold(self, service):
        """Test duplicate threshold check."""
        assert service.is_duplicate(0.9) is True
        assert service.is_duplicate(0.85) is True
        assert service.is_duplicate(0.84) is False
        assert service.is_duplicate(0.0) is False


class TestDuplicateCheckServiceIntegration:
    """Integration tests with mock receipts."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service with mock session."""
        return DuplicateCheckService(mock_session)

    @pytest.fixture
    def source_receipt(self):
        """Create source receipt for testing."""
        return Receipt(
            id=1,
            original_filename="test1.jpg",
            stored_filename="test1.jpg",
            file_path="/path/test1.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
            ocr_text="店舗A\n合計 1000円",
            ocr_confidence=90.0,
            receipt_date=datetime(2026, 7, 15, 12, 0),
            store_name="店舗A",
            total_amount=1000,
            tax_amount=100,
            currency="JPY",
            category_id=1,
            category_confidence=0.9,
            status=ReceiptStatus.UNAPPROVED,
        )

    @pytest.fixture
    def target_receipt(self):
        """Create target receipt for testing."""
        return Receipt(
            id=2,
            original_filename="test2.jpg",
            stored_filename="test2.jpg",
            file_path="/path/test2.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
            ocr_text="店舗A\n合計 1000円",
            ocr_confidence=85.0,
            receipt_date=datetime(2026, 7, 15, 13, 0),
            store_name="店舗A",
            total_amount=1000,
            tax_amount=100,
            currency="JPY",
            category_id=1,
            category_confidence=0.85,
            status=ReceiptStatus.APPROVED,
        )

    @pytest.mark.asyncio
    async def test_check_duplicate_exact_match(self, service, source_receipt, target_receipt):
        """Test duplicate check with exact match."""
        result = await service.check_duplicate(
            source_receipt, target_receipt, save_result=False
        )

        assert result.is_duplicate is True
        assert result.composite_score >= DEFAULT_DUPLICATE_THRESHOLD
        assert result.score_components.has_sufficient_data is True

    @pytest.mark.asyncio
    async def test_check_duplicate_insufficient_data(self, service):
        """Test duplicate check with insufficient data."""
        source = Receipt(
            id=1,
            original_filename="test.jpg",
            stored_filename="test.jpg",
            file_path="/path/test.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
            status=ReceiptStatus.UNAPPROVED,
        )
        target = Receipt(
            id=2,
            original_filename="test2.jpg",
            stored_filename="test2.jpg",
            file_path="/path/test2.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="def456",
            status=ReceiptStatus.APPROVED,
        )

        result = await service.check_duplicate(source, target, save_result=False)

        # Both receipts have minimal data
        assert result.is_duplicate is False
        assert result.score_components.has_sufficient_data is False
        assert result.composite_score == 0.0

    @pytest.mark.asyncio
    async def test_check_duplicate_saves_result(self, service, mock_session, source_receipt, target_receipt):
        """Test that duplicate check saves result when requested."""
        await service.check_duplicate(
            source_receipt, target_receipt, save_result=True
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()


class TestDuplicateScoreComponents:
    """Tests for DuplicateScoreComponents dataclass."""

    def test_creation(self):
        """Test creation with all fields."""
        comp = DuplicateScoreComponents(
            store_name_score=0.9,
            amount_score=1.0,
            date_score=1.0,
            metadata_score=0.8,
            image_hash_score=1.0,
            ocr_similarity_score=0.9,
            composite_score=0.95,
            has_sufficient_data=True,
        )
        assert comp.store_name_score == 0.9
        assert comp.has_sufficient_data is True


class TestDuplicateCheckResult:
    """Tests for DuplicateCheckResult dataclass."""

    def test_success_result(self):
        """Test successful check result."""
        components = DuplicateScoreComponents(
            store_name_score=0.9,
            amount_score=1.0,
            date_score=1.0,
            metadata_score=0.8,
            image_hash_score=1.0,
            ocr_similarity_score=0.9,
            composite_score=0.95,
            has_sufficient_data=True,
        )
        result = DuplicateCheckResult(
            is_duplicate=True,
            composite_score=0.95,
            score_components=components,
            duplicate_check_id=1,
        )
        assert result.is_duplicate is True
        assert result.duplicate_check_id == 1

    def test_error_result(self):
        """Test error result."""
        components = DuplicateScoreComponents(
            store_name_score=None,
            amount_score=None,
            date_score=None,
            metadata_score=None,
            image_hash_score=None,
            ocr_similarity_score=None,
            composite_score=0.0,
            has_sufficient_data=False,
        )
        result = DuplicateCheckResult(
            is_duplicate=False,
            composite_score=0.0,
            score_components=components,
            error="Test error",
        )
        assert result.error == "Test error"