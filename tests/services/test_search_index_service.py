"""Tests for SearchIndexService."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.receipt import Receipt, ReceiptStatus
from app.services.search_index_service import (
    SearchIndexService,
    SearchResult,
    SearchIndexStats,
)
from app.api.v1.dependencies import get_search_index_service


class TestSearchIndexService:
    """Tests for SearchIndexService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance."""
        return SearchIndexService(mock_session)

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
            ocr_text="店舗A\n合計 1000円",
            ocr_confidence=90.0,
            receipt_date=datetime(2026, 7, 15),
            store_name="店舗A",
            total_amount=1000,
            tax_amount=100,
            currency="JPY",
            category_id=1,
            category_confidence=0.9,
            ai_comment="日用品",
            ai_confidence=0.85,
            status=ReceiptStatus.APPROVED,
        )

    @pytest.mark.asyncio
    async def test_initialize(self, service, mock_session):
        """Test index initialization."""
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result

        await service.initialize()

        # Should have executed FTS table creation
        assert mock_session.execute.call_count >= 1
        mock_session.commit.assert_awaited_once()
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, service, mock_session):
        """Test that initialize is idempotent."""
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result

        await service.initialize()
        await service.initialize()

        # Should only execute once
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_index_receipt(self, service, mock_session, sample_receipt):
        """Test indexing a receipt."""
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result

        # First call initialize
        await service.initialize()

        result = await service.index_receipt(sample_receipt)

        assert result is True
        mock_session.execute.assert_called()
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_index_receipt_failure(self, service, mock_session, sample_receipt):
        """Test indexing failure handling."""
        # First call initialize successfully
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result
        await service.initialize()
        
        # Then make the insert fail
        mock_session.execute.side_effect = Exception("DB error")

        result = await service.index_receipt(sample_receipt)

        assert result is False
        mock_session.rollback.assert_awaited()

    @pytest.mark.asyncio
    async def test_remove_from_index(self, service, mock_session):
        """Test removing receipt from index."""
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result

        await service.initialize()

        result = await service.remove_from_index(1)

        assert result is True
        mock_session.execute.assert_called()
        mock_session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_search(self, service, mock_session, sample_receipt):
        """Test search functionality."""
        # Mock search results
        mock_row = MagicMock()
        mock_row.receipt_id = 1
        mock_row.store_name = "店舗A"
        mock_row.ocr_text = "店舗A\n合計 1000円"
        mock_row.ai_comment = "日用品"
        mock_row.tags = "食事,出張"
        mock_row.category_name = "category_1"
        mock_row.total_amount = 1000
        mock_row.receipt_date = datetime(2026, 7, 15)
        mock_row.score = 0.5  # BM25 score

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        await service.initialize()

        results = await service.search("店舗A", limit=10)

        assert len(results) == 1
        assert results[0].receipt_id == 1
        assert results[0].store_name == "店舗A"
        assert 0.0 < results[0].score <= 1.0

    @pytest.mark.asyncio
    async def test_search_no_results(self, service, mock_session):
        """Test search with no results."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        await service.initialize()

        results = await service.search("存在しない店舗")

        assert results == []

    def test_build_fts_query(self, service):
        """Test FTS query building."""
        query = service._build_fts_query("テスト 検索")
        # Terms should be quoted for phrase matching
        assert '"テスト"' in query or "テスト" in query
        assert '"検索"' in query or "検索" in query

    def test_build_fts_query_empty(self, service):
        """Test FTS query with empty string."""
        query = service._build_fts_query("")
        assert query == '""'

    def test_generate_snippet(self, service):
        """Test snippet generation."""
        ocr_text = "店舗A\n商品1 500円\n商品2 500円\n合計 1000円"
        ai_comment = "日用品購入"
        query = "店舗A"

        snippet = service._generate_snippet(query, ocr_text, ai_comment)

        assert "店舗A" in snippet
        assert len(snippet) <= 250  # Reasonable length

    def test_generate_snippet_no_match(self, service):
        """Test snippet generation with no match."""
        ocr_text = "長いテキストがここにあります。" * 10
        query = "存在しない"

        snippet = service._generate_snippet(query, ocr_text, "")

        # Should return beginning of text
        assert snippet.startswith("長いテキスト")


class TestSearchIndexServiceRebuild:
    """Tests for index rebuilding."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance."""
        return SearchIndexService(mock_session)

    @pytest.mark.asyncio
    async def test_rebuild_index(self, service, mock_session):
        """Test rebuilding the search index."""
        # Mock receipt data
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.store_name = "店舗A"
        mock_row.ocr_text = "テキスト"
        mock_row.ai_comment = "コメント"
        mock_row.category_id = 1
        mock_row.tags = ["タグ1"]

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        await service.initialize()

        count = await service.rebuild_index()

        assert count == 1
        assert mock_session.execute.call_count >= 2  # DELETE + INSERT
        mock_session.commit.assert_awaited()


class TestSearchIndexStats:
    """Tests for SearchIndexStats."""

    def test_creation(self):
        """Test stats creation."""
        stats = SearchIndexStats(
            total_documents=100,
            last_updated=datetime.now(),
            index_size_bytes=1024000,
        )
        assert stats.total_documents == 100
        assert stats.index_size_bytes == 1024000


class TestGetSearchIndexService:
    """Tests for get_search_index_service helper."""

    def test_returns_instance(self):
        """Test that helper returns service instance."""
        mock_session = AsyncMock()
        service = get_search_index_service(mock_session)
        assert isinstance(service, SearchIndexService)