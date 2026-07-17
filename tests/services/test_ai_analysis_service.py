"""Tests for AI Analysis Service."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.ai_analysis_service import (
    AIAnalysisError,
    AIAnalysisResponse,
    AIAnalysisService,
    OpenRouterClient,
    PromptBuilder,
    ReceiptData,
    RetryConfig,
)
from app.core.constants import AccountCategory


class TestReceiptData:
    """Tests for ReceiptData model."""

    def test_receipt_data_creation_minimal(self) -> None:
        """Test ReceiptData with minimal fields."""
        data = ReceiptData()
        assert data.receipt_date is None
        assert data.store_name is None
        assert data.total_amount is None
        assert data.currency == "JPY"
        assert data.tags == []
        assert data.category_confidence == 0.0
        assert data.ai_confidence == 0.0

    def test_receipt_data_creation_full(self) -> None:
        """Test ReceiptData with all fields."""
        data = ReceiptData(
            receipt_date="2026-07-15",
            store_name="テストスーパー",
            total_amount=1500,
            tax_amount=150,
            currency="JPY",
            category="消耗品費",
            category_confidence=0.9,
            tags=["食事", "出張"],
            ai_comment="昼食代として計上",
            ai_confidence=0.85,
        )
        assert data.receipt_date == "2026-07-15"
        assert data.store_name == "テストスーパー"
        assert data.total_amount == 1500
        assert data.tax_amount == 150
        assert data.category == "消耗品費"
        assert data.tags == ["食事", "出張"]

    def test_receipt_data_validation_category_confidence(self) -> None:
        """Test category_confidence validation bounds."""
        with pytest.raises(ValueError):
            ReceiptData(category_confidence=1.5)
        with pytest.raises(ValueError):
            ReceiptData(category_confidence=-0.1)

    def test_receipt_data_validation_ai_confidence(self) -> None:
        """Test ai_confidence validation bounds."""
        with pytest.raises(ValueError):
            ReceiptData(ai_confidence=1.5)
        with pytest.raises(ValueError):
            ReceiptData(ai_confidence=-0.1)


class TestAIAnalysisResponse:
    """Tests for AIAnalysisResponse model."""

    def test_success_response(self) -> None:
        """Test successful response creation."""
        data = ReceiptData(store_name="テスト店", total_amount=1000)
        response = AIAnalysisResponse(
            success=True,
            data=data,
            error=None,
            model="test-model",
            processing_time_ms=1000,
        )
        assert response.success is True
        assert response.data is not None
        assert response.error is None

    def test_error_response(self) -> None:
        """Test error response creation."""
        response = AIAnalysisResponse(
            success=False,
            data=None,
            error="API timeout",
            model="test-model",
            processing_time_ms=5000,
        )
        assert response.success is False
        assert response.data is None
        assert response.error == "API timeout"


class TestPromptBuilder:
    """Tests for PromptBuilder."""

    def test_build_receipt_prompt(self) -> None:
        """Test receipt prompt building."""
        prompt = PromptBuilder.build_receipt_prompt(
            ocr_text="テスト店舗\n合計 1000円",
            image_path="/path/to/image.jpg",
        )
        assert "テスト店舗" in prompt
        assert "1000円" in prompt
        assert "/path/to/image.jpg" in prompt
        assert "JSON形式で返してください" in prompt

    def test_build_category_prompt(self) -> None:
        """Test category classification prompt building."""
        prompt = PromptBuilder.build_category_prompt(
            store_name="テスト店",
            total_amount=2000,
            ocr_text="テスト店舗\n合計 2000円",
        )
        assert "テスト店" in prompt
        assert "2000" in prompt
        assert "勘定科目候補" in prompt
        assert "JSON形式で返却" in prompt


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self) -> None:
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0

    def test_custom_values(self) -> None:
        """Test custom retry configuration."""
        config = RetryConfig(max_retries=5, base_delay=2.0, max_delay=60.0)
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0


class TestOpenRouterClient:
    """Tests for OpenRouterClient."""

    @pytest.fixture
    def client(self) -> OpenRouterClient:
        """Create client with mocked settings."""
        with patch("app.services.ai_analysis_service.get_settings") as mock_settings:
            mock_settings.return_value.openrouter_api_key = "test-key"
            mock_settings.return_value.openrouter_base_url = "https://api.test.com/v1"
            mock_settings.return_value.openrouter_model = "test/model"
            mock_settings.return_value.openrouter_timeout = 30
            return OpenRouterClient()

    @pytest.mark.asyncio
    async def test_get_client_creates_async_client(self, client: OpenRouterClient) -> None:
        """Test _get_client creates httpx.AsyncClient."""
        http_client = await client._get_client()
        assert isinstance(http_client, httpx.AsyncClient)
        assert "Authorization" in http_client.headers
        assert http_client.headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_close_client(self, client: OpenRouterClient) -> None:
        """Test close closes the HTTP client."""
        await client._get_client()
        await client.close()
        assert client._client is None or client._client.is_closed

    @pytest.mark.asyncio
    async def test_analyze_receipt_success(self, client: OpenRouterClient) -> None:
        """Test successful API call."""
        mock_response = {
            "choices": [{"message": {"content": '{"store_name": "Test", "total_amount": 1000}'}}]
        }

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client_obj = AsyncMock()
            mock_client_obj.post = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: mock_response,
                    raise_for_status=lambda: None,
                )
            )
            mock_get_client.return_value = mock_client_obj

            result = await client.analyze_receipt("test prompt")
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_analyze_receipt_timeout(self, client: OpenRouterClient) -> None:
        """Test API timeout handling."""
        with patch.object(client, "_get_client") as mock_get_client:
            mock_client_obj = AsyncMock()
            mock_client_obj.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_client_obj

            with pytest.raises(AIAnalysisError) as exc_info:
                await client.analyze_receipt("test prompt")
            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_analyze_receipt_http_error(self, client: OpenRouterClient) -> None:
        """Test HTTP error handling."""
        with patch.object(client, "_get_client") as mock_get_client:
            mock_client_obj = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client_obj.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "401 Unauthorized", request=MagicMock(), response=mock_response
                )
            )
            mock_get_client.return_value = mock_client_obj

            with pytest.raises(AIAnalysisError) as exc_info:
                await client.analyze_receipt("test prompt")
            assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_receipt_no_api_key(self, client: OpenRouterClient) -> None:
        """Test error when API key not configured."""
        client._api_key = ""
        with pytest.raises(AIAnalysisError) as exc_info:
            await client.analyze_receipt("test prompt")
        assert "not configured" in str(exc_info.value).lower()


class TestAIAnalysisService:
    """Tests for AIAnalysisService."""

    @pytest.fixture
    def service(self) -> AIAnalysisService:
        """Create service with mocked client."""
        mock_client = AsyncMock(spec=OpenRouterClient)
        retry_config = RetryConfig(max_retries=2, base_delay=0.01, max_delay=0.1)
        return AIAnalysisService(retry_config=retry_config, client=mock_client)

    @pytest.fixture
    def temp_image(self) -> Path:
        """Create a temporary image file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image content")
            return Path(f.name)

    @pytest.mark.asyncio
    async def test_analyze_receipt_success(
        self, service: AIAnalysisService, temp_image: Path
    ) -> None:
        """Test successful receipt analysis."""
        mock_response = AIAnalysisResponse(
            success=True,
            data=ReceiptData(
                store_name="テスト店",
                total_amount=1500,
                category="消耗品費",
                category_confidence=0.9,
                tags=["食事"],
                ai_comment="昼食",
                ai_confidence=0.85,
            ),
            error=None,
            model="test-model",
            processing_time_ms=1000,
        )
        service._perform_analysis = AsyncMock(return_value=mock_response)

        # Mock time.perf_counter to return increasing values
        with patch("time.perf_counter", side_effect=[0.0, 1.5]):
            result = await service.analyze_receipt("OCR text", str(temp_image), receipt_id=1)

        assert result.success is True
        assert result.data is not None
        assert result.data.store_name == "テスト店"
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_analyze_receipt_retry_on_failure(
        self, service: AIAnalysisService, temp_image: Path
    ) -> None:
        """Test retry logic on failure."""
        error = AIAnalysisError("API error")
        service._perform_analysis = AsyncMock(
            side_effect=[error, error, AIAnalysisResponse(
                success=True,
                data=ReceiptData(store_name="Success"),
                error=None,
                model="test-model",
                processing_time_ms=0,
            )]
        )

        result = await service.analyze_receipt("OCR text", str(temp_image))

        assert result.success is True
        assert service._perform_analysis.call_count == 3

    @pytest.mark.asyncio
    async def test_analyze_receipt_all_retries_exhausted(
        self, service: AIAnalysisService, temp_image: Path
    ) -> None:
        """Test failure after all retries exhausted."""
        error = AIAnalysisError("Persistent error")
        service._perform_analysis = AsyncMock(side_effect=error)

        result = await service.analyze_receipt("OCR text", str(temp_image))

        assert result.success is False
        assert "failed after" in result.error.lower()
        assert service._perform_analysis.call_count == 3  # max_retries + 1

    @pytest.mark.asyncio
    async def test_analyze_receipt_empty_ocr_text(
        self, service: AIAnalysisService, temp_image: Path
    ) -> None:
        """Test handling of empty OCR text."""
        result = await service.analyze_receipt("", str(temp_image))

        assert result.success is False
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_classify_category_success(self, service: AIAnalysisService) -> None:
        """Test category classification."""
        mock_response = {
            "choices": [{"message": {"content": '{"category": "旅費交通費", "confidence": 0.85}'}}]
        }
        service._client.analyze_receipt = AsyncMock(return_value=mock_response)

        category, confidence = await service.classify_category("駅", 500, "電車代 500円")

        assert category == "旅費交通費"
        assert confidence == 0.85

    @pytest.mark.asyncio
    async def test_classify_category_invalid_category(
        self, service: AIAnalysisService
    ) -> None:
        """Test classification with invalid category falls back to その他."""
        mock_response = {
            "choices": [{"message": {"content": '{"category": "InvalidCategory", "confidence": 0.9}'}}]
        }
        service._client.analyze_receipt = AsyncMock(return_value=mock_response)

        category, confidence = await service.classify_category("店", 1000, "text")

        assert category == AccountCategory.OTHER.value
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_classify_category_exception_fallback(
        self, service: AIAnalysisService
    ) -> None:
        """Test classification falls back on exception."""
        service._client.analyze_receipt = AsyncMock(side_effect=Exception("API error"))

        category, confidence = await service.classify_category("店", 1000, "text")

        assert category == AccountCategory.OTHER.value
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_close(self, service: AIAnalysisService) -> None:
        """Test closing the service closes the client."""
        await service.close()
        service._client.close.assert_called_once()


class TestAIAnalysisError:
    """Tests for AIAnalysisError."""

    def test_error_with_retry_count(self) -> None:
        """Test error stores retry count."""
        error = AIAnalysisError("Test error", retry_count=2)
        assert error.retry_count == 2

    def test_error_with_original_error(self) -> None:
        """Test error stores original exception."""
        original = ValueError("Original")
        error = AIAnalysisError("Test error", original_error=original)
        assert error.original_error is original

    def test_error_with_retry_count_method(self) -> None:
        """Test with_retry_count method creates new error with updated count."""
        error = AIAnalysisError("Test error", retry_count=0)
        new_error = error.with_retry_count(2)
        assert new_error.retry_count == 2
        assert new_error.original_error is error.original_error