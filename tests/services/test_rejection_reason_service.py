"""Tests for RejectionReasonService."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import func

from app.core.constants import ReceiptStatus
from app.models.receipt import Receipt
from app.models.rejection_reason import RejectionReason
from app.services.rejection_reason_service import (
    RejectionReasonService,
    RejectionData,
    RejectionResult,
    RejectionReasonCode,
    RejectionCategory,
    REJECTION_CODE_TO_CATEGORY,
    get_rejection_reason_service,
)


class TestRejectionReasonService:
    """Tests for RejectionReasonService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.get = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance."""
        return RejectionReasonService(mock_session)

    @pytest.fixture
    def sample_receipt(self):
        """Create sample receipt."""
        return Receipt(
            id=1,
            original_filename="receipt.jpg",
            stored_filename="receipt.jpg",
            file_path="/tmp/receipt.jpg",
            file_size=1000,
            mime_type="image/jpeg",
            image_hash="abc123",
            status=ReceiptStatus.UNAPPROVED,
        )

    def test_get_category_for_code(self):
        """Test category lookup for known codes."""
        assert RejectionReasonService.get_category_for_code("poor_image_quality") == RejectionCategory.IMAGE_QUALITY
        assert RejectionReasonService.get_category_for_code("ocr_failed") == RejectionCategory.OCR_AI
        assert RejectionReasonService.get_category_for_code("duplicate_receipt") == RejectionCategory.DATA_VALIDITY
        assert RejectionReasonService.get_category_for_code("non_deductible") == RejectionCategory.BUSINESS_RULE
        assert RejectionReasonService.get_category_for_code("user_cancelled") == RejectionCategory.USER_ACTION

    def test_get_category_for_unknown_code(self):
        """Test category lookup for unknown code defaults to OTHER."""
        assert RejectionReasonService.get_category_for_code("unknown_code") == RejectionCategory.OTHER

    def test_validate_reason_code(self):
        """Test reason code validation."""
        assert RejectionReasonService.validate_reason_code("poor_image_quality") is True
        assert RejectionReasonService.validate_reason_code("ocr_failed") is True
        assert RejectionReasonService.validate_reason_code("invalid_code") is False

    @pytest.mark.asyncio
    async def test_create_rejection_reason_success(self, service, mock_session, sample_receipt):
        """Test successful rejection reason creation."""
        mock_session.get.return_value = sample_receipt

        # Mock flush to assign ID to the added object
        async def mock_flush():
            # Find the added RejectionReason and assign ID
            for call in mock_session.add.call_args_list:
                obj = call[0][0]
                if isinstance(obj, RejectionReason):
                    obj.id = 1
                    break

        mock_session.flush.side_effect = mock_flush

        data = RejectionData(
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_text="画像がぼやけていて読み取れません",
            user_note="再撮影が必要",
            is_for_ai_training=True,
        )

        result = await service.create_rejection_reason(data)

        assert result.success is True
        assert result.rejection_reason_id is not None
        assert sample_receipt.status == ReceiptStatus.REJECTED
        mock_session.add.assert_called()
        mock_session.flush.assert_awaited()
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_create_rejection_reason_receipt_not_found(self, service, mock_session):
        """Test rejection reason creation with missing receipt."""
        mock_session.get.return_value = None

        data = RejectionData(
            receipt_id=999,
            reason_code="poor_image_quality",
            reason_text="理由",
        )

        result = await service.create_rejection_reason(data)

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_create_rejection_reason_already_rejected(self, service, mock_session, sample_receipt):
        """Test rejection of already rejected receipt."""
        sample_receipt.status = ReceiptStatus.REJECTED
        mock_session.get.return_value = sample_receipt

        data = RejectionData(
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_text="理由",
        )

        result = await service.create_rejection_reason(data)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_create_rejection_reason_already_approved(self, service, mock_session, sample_receipt):
        """Test rejection of already approved receipt."""
        sample_receipt.status = ReceiptStatus.APPROVED
        mock_session.get.return_value = sample_receipt

        data = RejectionData(
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_text="理由",
        )

        result = await service.create_rejection_reason(data)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_get_rejection_reason(self, service, mock_session):
        """Test retrieving rejection reason."""
        reason = RejectionReason(
            id=1,
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_category="image_quality",
            reason_text="ぼやけている",
            user_note="再撮影",
            is_for_ai_training=True,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = reason
        mock_session.execute.return_value = mock_result

        result = await service.get_rejection_reason(1)

        assert result is not None
        assert result.reason_code == "poor_image_quality"
        assert result.is_for_ai_training is True

    @pytest.mark.asyncio
    async def test_get_rejection_reason_not_found(self, service, mock_session):
        """Test retrieving non-existent rejection reason."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_rejection_reason(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_rejection_reasons_with_filters(self, service, mock_session):
        """Test listing rejection reasons with filters."""
        reasons = [
            RejectionReason(
                id=1,
                receipt_id=1,
                reason_code="poor_image_quality",
                reason_category="image_quality",
                reason_text="ぼやけている",
                created_at=datetime.now(),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = reasons
        mock_session.execute.return_value = mock_result

        results = await service.get_rejection_reasons(
            category=RejectionCategory.IMAGE_QUALITY,
            limit=10,
            offset=0,
        )

        assert len(results) == 1
        assert results[0].reason_code == "poor_image_quality"
        # Verify the query was executed
        mock_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_ai_training_flag(self, service, mock_session):
        """Test updating AI training flag."""
        reason = RejectionReason(
            id=1,
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_category="image_quality",
            reason_text="ぼやけている",
            is_for_ai_training=False,
        )
        mock_session.get.return_value = reason

        result = await service.update_ai_training_flag(1, True, "AI学習用フィードバック")

        assert result is True
        assert reason.is_for_ai_training is True
        assert reason.ai_feedback == "AI学習用フィードバック"
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_ai_training_flag_not_found(self, service, mock_session):
        """Test updating AI training flag for non-existent reason."""
        mock_session.get.return_value = None

        result = await service.update_ai_training_flag(999, True)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_stats(self, service, mock_session):
        """Test getting rejection statistics."""
        # Mock total count
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 100

        # Mock category breakdown
        mock_cat_result = MagicMock()
        mock_cat_result.fetchall.return_value = [
            ("image_quality", 30),
            ("ocr_ai", 25),
            ("data_validity", 20),
            ("business_rule", 15),
            ("user_action", 10),
        ]

        # Mock code breakdown
        mock_code_result = MagicMock()
        mock_code_result.fetchall.return_value = [
            ("poor_image_quality", 15),
            ("blurry_image", 15),
            ("ocr_failed", 20),
        ]

        # Mock AI training eligible
        mock_ai_result = MagicMock()
        mock_ai_result.scalar.return_value = 40

        mock_session.execute.side_effect = [
            mock_total_result,
            mock_cat_result,
            mock_code_result,
            mock_ai_result,
        ]

        stats = await service.get_stats()

        assert stats["total"] == 100
        assert stats["by_category"]["image_quality"] == 30
        assert stats["by_reason_code"]["poor_image_quality"] == 15
        assert stats["ai_training_eligible"] == 40

    @pytest.mark.asyncio
    async def test_export_ai_training_data(self, service, mock_session):
        """Test exporting AI training data."""
        reasons = [
            RejectionReason(
                id=1,
                receipt_id=1,
                reason_code="poor_image_quality",
                reason_category="image_quality",
                reason_text="ぼやけている",
                user_note="再撮影",
                ai_feedback="画質向上が必要",
                is_for_ai_training=True,
                created_at=datetime(2026, 7, 15),
            ),
            RejectionReason(
                id=2,
                receipt_id=2,
                reason_code="ocr_failed",
                reason_category="ocr_ai",
                reason_text="OCR失敗",
                user_note=None,
                ai_feedback=None,
                is_for_ai_training=True,
                created_at=datetime(2026, 7, 14),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = reasons
        mock_session.execute.return_value = mock_result

        data = await service.export_ai_training_data()

        assert len(data) == 2
        assert data[0]["receipt_id"] == 1
        assert data[0]["reason_code"] == "poor_image_quality"
        assert data[0]["is_for_ai_training"] is True


class TestRejectionData:
    """Tests for RejectionData dataclass."""

    def test_creation(self):
        """Test RejectionData creation."""
        data = RejectionData(
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_text="ぼやけている",
            user_note="メモ",
            is_for_ai_training=True,
        )

        assert data.receipt_id == 1
        assert data.reason_code == "poor_image_quality"
        assert data.reason_text == "ぼやけている"
        assert data.user_note == "メモ"
        assert data.is_for_ai_training is True
        assert data.ai_feedback is None

    def test_optional_fields(self):
        """Test optional fields default to None."""
        data = RejectionData(
            receipt_id=1,
            reason_code="poor_image_quality",
            reason_text="ぼやけている",
        )

        assert data.user_note is None
        assert data.ai_feedback is None
        assert data.is_for_ai_training is False


class TestRejectionResult:
    """Tests for RejectionResult dataclass."""

    def test_success(self):
        """Test success result."""
        result = RejectionResult(success=True, rejection_reason_id=1)
        assert result.success is True
        assert result.rejection_reason_id == 1
        assert result.error is None

    def test_failure(self):
        """Test failure result."""
        result = RejectionResult(success=False, error="エラーが発生しました")
        assert result.success is False
        assert result.rejection_reason_id is None
        assert result.error == "エラーが発生しました"


class TestGetRejectionReasonService:
    """Tests for get_rejection_reason_service helper."""

    @pytest.mark.asyncio
    async def test_returns_instance(self):
        """Test that helper returns service instance."""
        mock_session = AsyncMock()
        service = await get_rejection_reason_service(mock_session)
        assert isinstance(service, RejectionReasonService)