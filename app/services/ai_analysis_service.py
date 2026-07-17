"""AI Analysis Service for receipt data extraction using OpenRouter API.

Implements RULE-BE-003: Receipt image analysis (date, store, amount, category, tags, AI comment).
Implements RULE-BE-012: AI analysis API retry logic (RULE-ERR-001).
Implements RULE-BE-014: External API (OpenRouter) calling implementation.
Implements RULE-ERR-001: Retry on failure, move to failed folder on 3 retries, notify WebUI.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import get_settings
from app.core.constants import AccountCategory
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIAnalysisRequest(BaseModel):
    """Request model for AI analysis.

    Attributes:
        ocr_text: Text extracted from OCR.
        image_path: Path to the receipt image (for context).
    """

    ocr_text: str = Field(..., description="OCR extracted text from receipt")
    image_path: str = Field(..., description="Path to receipt image file")


class ReceiptData(BaseModel):
    """Structured receipt data extracted by AI.

    Attributes:
        receipt_date: Date of the receipt (ISO format).
        store_name: Name of the store/merchant.
        total_amount: Total amount in yen (integer).
        tax_amount: Tax amount in yen (optional).
        currency: Currency code (default JPY).
        category: Account category (勘定科目).
        category_confidence: Confidence score for category (0.0-1.0).
        tags: List of tags for the receipt.
        ai_comment: AI-generated comment/analysis.
        ai_confidence: Overall confidence score (0.0-1.0).
    """

    receipt_date: Optional[str] = Field(None, description="Receipt date in ISO format")
    store_name: Optional[str] = Field(None, description="Store/merchant name")
    total_amount: Optional[int] = Field(None, description="Total amount in yen")
    tax_amount: Optional[int] = Field(None, description="Tax amount in yen")
    currency: str = Field(default="JPY", description="Currency code")
    category: Optional[str] = Field(None, description="Account category")
    category_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list, description="Receipt tags")
    ai_comment: Optional[str] = Field(None, description="AI analysis comment")
    ai_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AIAnalysisResponse(BaseModel):
    """Response model for AI analysis.

    Attributes:
        success: Whether analysis succeeded.
        data: Extracted receipt data.
        error: Error message if failed.
        model: AI model used.
        processing_time_ms: Processing time in milliseconds.
    """

    success: bool = Field(..., description="Analysis success flag")
    data: Optional[ReceiptData] = Field(None, description="Extracted receipt data")
    error: Optional[str] = Field(None, description="Error message if failed")
    model: str = Field(..., description="AI model used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Configuration for retry logic.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
        max_delay: Maximum delay in seconds.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0


class AIAnalysisError(Exception):
    """Custom exception for AI analysis errors."""

    def __init__(
        self,
        message: str,
        *,
        retry_count: int = 0,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.retry_count = retry_count
        self.original_error = original_error


class OpenRouterClient:
    """Client for OpenRouter API calls.

    Single responsibility: Handle HTTP communication with OpenRouter API.
    """

    def __init__(self) -> None:
        """Initialize OpenRouter client with settings."""
        self._settings = get_settings()
        self._base_url = self._settings.openrouter_base_url.rstrip("/")
        self._api_key = self._settings.openrouter_api_key
        self._model = self._settings.openrouter_model
        self._timeout = self._settings.openrouter_timeout
        self._client: Optional[httpx.AsyncClient] = None

        if not self._api_key:
            logger.warning("OpenRouter API key not configured")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://receipt-system.local",
                    "X-Title": "Receipt System",
                },
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def analyze_receipt(self, prompt: str) -> dict[str, Any]:
        """Call OpenRouter API for receipt analysis.

        Args:
            prompt: Formatted prompt for receipt analysis.

        Returns:
            Parsed JSON response from API.

        Raises:
            AIAnalysisError: On API errors or invalid responses.
        """
        if not self._api_key:
            raise AIAnalysisError("OpenRouter API key not configured")

        client = await self._get_client()

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt(),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        }

        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            raise AIAnalysisError("OpenRouter API timeout", original_error=e) from e
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except Exception:
                pass
            raise AIAnalysisError(
                f"OpenRouter API error: {e.response.status_code} - {error_detail}",
                original_error=e,
            ) from e
        except httpx.RequestError as e:
            raise AIAnalysisError("OpenRouter API request failed", original_error=e) from e

    def _get_system_prompt(self) -> str:
        """Get system prompt for receipt analysis."""
        categories = ", ".join([c.value for c in AccountCategory])
        return f"""あなたはレシート解析の専門家です。OCRで抽出されたテキストから以下の情報を抽出し、JSON形式で返してください。

抽出項目:
1. receipt_date: レシートの日付 (ISO形式 YYYY-MM-DD、不明ならnull)
2. store_name: 店舗名 (不明ならnull)
3. total_amount: 合計金額（円、整数、不明ならnull）
4. tax_amount: 税額（円、整数、不明ならnull）
5. currency: 通貨コード (デフォルト "JPY")
6. category: 勘定科目 (以下から選択: {categories}。不明なら"その他")
7. category_confidence: カテゴリ判定の確信度 (0.0-1.0)
8. tags: 関連タグの配列 (例: ["食事", "出張", "接待"] など)
9. ai_comment: AIによる分析コメント・備考
10. ai_confidence: 全体的な解析確信度 (0.0-1.0)

重要:
- 金額は円単位の整数で返す
- 日付が不明な場合はnullを返す
- カテゴリは上記リストから必ず選択する
- JSONのみを返す（説明文は不要）"""


class PromptBuilder:
    """Builds prompts for AI analysis.

    Single responsibility: Format OCR text into prompts for AI analysis.
    """

    @staticmethod
    def build_receipt_prompt(ocr_text: str, image_path: str) -> str:
        """Build prompt for receipt analysis.

        Args:
            ocr_text: Text extracted from OCR.
            image_path: Path to the receipt image.

        Returns:
            Formatted prompt string.
        """
        return f"""以下のOCRテキストはレシート画像から抽出されたものです。
画像パス: {image_path}

OCRテキスト:
```
{ocr_text}
```

上記のテキストからレシート情報を抽出し、指定されたJSON形式で返してください。"""

    @staticmethod
    def build_category_prompt(
        store_name: Optional[str],
        total_amount: Optional[int],
        ocr_text: str,
    ) -> str:
        """Build prompt for category classification.

        Args:
            store_name: Store name from receipt.
            total_amount: Total amount.
            ocr_text: Full OCR text.

        Returns:
            Formatted prompt for category classification.
        """
        categories = ", ".join([c.value for c in AccountCategory])
        return f"""以下のレシート情報から最も適切な勘定科目を判定してください。

店舗名: {store_name or "不明"}
合計金額: {total_amount or "不明"}円
OCRテキスト:
```
{ocr_text[:2000]}
```

勘定科目候補: {categories}

JSON形式で返却:
{{
  "category": "勘定科目名",
  "confidence": 0.0-1.0,
  "reason": "判定理由"
}}"""


class AIAnalysisService:
    """Service for AI-powered receipt analysis using OpenRouter.

    Implements RULE-BE-003: Receipt analysis (date, store, amount, category, tags, AI comment).
    Implements RULE-BE-012: Retry logic (RULE-ERR-001).
    Implements RULE-BE-014: OpenRouter API integration.
    Implements RULE-ERR-001: Retry 3 times, move to failed folder, notify WebUI.
    Single responsibility: Orchestrate AI analysis with retry logic.
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        client: Optional[OpenRouterClient] = None,
    ) -> None:
        """Initialize AI analysis service.

        Args:
            retry_config: Retry configuration.
            client: OpenRouter client (for testing).
        """
        self._settings = get_settings()
        self._retry_config = retry_config or RetryConfig(
            max_retries=self._settings.openrouter_max_retries,
        )
        self._client = client or OpenRouterClient()
        self._prompt_builder = PromptBuilder()
        logger.info(
            "AI Analysis service initialized",
            extra={
                "model": self._settings.openrouter_model,
                "max_retries": self._retry_config.max_retries,
            },
        )

    async def analyze_receipt(
        self,
        ocr_text: str,
        image_path: str,
        receipt_id: Optional[int] = None,
    ) -> AIAnalysisResponse:
        """Analyze receipt using AI with retry logic.

        Implements RULE-ERR-001: Retry up to 3 times on failure.

        Args:
            ocr_text: Text extracted from OCR.
            image_path: Path to receipt image.
            receipt_id: Optional receipt ID for logging.

        Returns:
            AIAnalysisResponse with extracted data or error.
        """
        start_time = time.perf_counter()
        last_error: Optional[Exception] = None

        for attempt in range(self._retry_config.max_retries + 1):
            try:
                logger.info(
                    "AI analysis attempt",
                    extra={
                        "receipt_id": receipt_id,
                        "attempt": attempt + 1,
                        "max_attempts": self._retry_config.max_retries + 1,
                    },
                )

                response = await self._perform_analysis(ocr_text, image_path)
                processing_time_ms = int((time.perf_counter() - start_time) * 1000)

                response.processing_time_ms = processing_time_ms

                logger.info(
                    "AI analysis completed",
                    extra={
                        "receipt_id": receipt_id,
                        "success": response.success,
                        "attempts": attempt + 1,
                        "processing_time_ms": processing_time_ms,
                    },
                )

                return response

            except AIAnalysisError as e:
                last_error = e
                logger.warning(
                    "AI analysis attempt failed",
                    extra={
                        "receipt_id": receipt_id,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                )

                if attempt < self._retry_config.max_retries:
                    delay = min(
                        self._retry_config.base_delay * (2**attempt),
                        self._retry_config.max_delay,
                    )
                    logger.info(
                        "Retrying AI analysis after delay",
                        extra={"delay_seconds": delay, "receipt_id": receipt_id},
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "AI analysis failed after all retries",
                        extra={
                            "receipt_id": receipt_id,
                            "total_attempts": attempt + 1,
                            "error": str(e),
                        },
                    )

        # All retries exhausted
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        error_msg = f"AI analysis failed after {self._retry_config.max_retries + 1} attempts"
        if last_error:
            error_msg += f": {last_error}"

        return AIAnalysisResponse(
            success=False,
            data=None,
            error=error_msg,
            model=self._settings.openrouter_model,
            processing_time_ms=processing_time_ms,
        )

    async def _perform_analysis(
        self, ocr_text: str, image_path: str
    ) -> AIAnalysisResponse:
        """Perform single AI analysis attempt.

        Args:
            ocr_text: OCR extracted text.
            image_path: Image file path.

        Returns:
            AIAnalysisResponse.

        Raises:
            AIAnalysisError: On analysis failure.
        """
        if not ocr_text or not ocr_text.strip():
            logger.warning("Empty OCR text provided for AI analysis")
            return AIAnalysisResponse(
                success=False,
                data=None,
                error="OCR text is empty",
                model=self._settings.openrouter_model,
                processing_time_ms=0,
            )

        prompt = self._prompt_builder.build_receipt_prompt(ocr_text, image_path)

        try:
            api_response = await self._client.analyze_receipt(prompt)
        except AIAnalysisError:
            raise
        except Exception as e:
            raise AIAnalysisError("Unexpected error during API call", original_error=e) from e

        # Parse API response
        try:
            content = api_response["choices"][0]["message"]["content"]
            parsed_data = json.loads(content)
            receipt_data = ReceiptData(**parsed_data)
        except (KeyError, IndexError, json.JSONDecodeError, ValidationError) as e:
            logger.error(
                "Failed to parse AI response",
                extra={"response": str(api_response)[:500], "error": str(e)},
            )
            raise AIAnalysisError("Failed to parse AI response", original_error=e) from e

        # Validate category
        if receipt_data.category and receipt_data.category not in [
            c.value for c in AccountCategory
        ]:
            logger.warning(
                "Invalid category from AI, defaulting to その他",
                extra={"category": receipt_data.category},
            )
            receipt_data.category = AccountCategory.OTHER.value
            receipt_data.category_confidence = 0.0

        return AIAnalysisResponse(
            success=True,
            data=receipt_data,
            error=None,
            model=self._settings.openrouter_model,
            processing_time_ms=0,  # Will be set by caller
        )

    async def classify_category(
        self,
        store_name: Optional[str],
        total_amount: Optional[int],
        ocr_text: str,
    ) -> tuple[str, float]:
        """Classify receipt category using AI.

        Implements RULE-BE-005: Category classification logic.

        Args:
            store_name: Store name.
            total_amount: Total amount.
            ocr_text: Full OCR text.

        Returns:
            Tuple of (category, confidence).
        """
        prompt = self._prompt_builder.build_category_prompt(
            store_name, total_amount, ocr_text
        )

        try:
            api_response = await self._client.analyze_receipt(prompt)
            content = api_response["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            category = parsed.get("category", AccountCategory.OTHER.value)
            confidence = float(parsed.get("confidence", 0.0))

            # Validate category
            valid_categories = [c.value for c in AccountCategory]
            if category not in valid_categories:
                category = AccountCategory.OTHER.value
                confidence = 0.0

            return category, confidence

        except Exception as e:
            logger.error(
                "Category classification failed",
                extra={"error": str(e)},
            )
            return AccountCategory.OTHER.value, 0.0

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()


async def get_ai_analysis_service() -> AIAnalysisService:
    """Get AI analysis service instance (dependency injection helper).

    Returns:
        AIAnalysisService instance.
    """
    return AIAnalysisService()