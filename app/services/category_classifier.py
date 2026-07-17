"""Category Classifier Service for receipt categorization.

Implements RULE-BE-005: Category classification logic based on AI analysis results.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.

This service provides rule-based and AI-assisted category classification.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from app.core.config import get_settings
from app.core.constants import AccountCategory
from app.core.logging import get_logger
from app.services.ai_analysis_service import AIAnalysisService

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class CategoryRule:
    """Rule for keyword-based category matching.

    Attributes:
        category: The account category.
        keywords: List of keywords that indicate this category.
        weight: Weight for this rule (higher = more specific).
    """

    category: AccountCategory
    keywords: tuple[str, ...]
    weight: float = 1.0


# Default category classification rules (keyword-based fallback)
DEFAULT_CATEGORY_RULES: tuple[CategoryRule, ...] = (
    CategoryRule(
        category=AccountCategory.TRAVEL_EXPENSE,
        keywords=(
            "交通",
            "電車",
            "バス",
            "タクシー",
            "新幹線",
            "飛行機",
            "高速",
            "駐車場",
            "ガソリン",
            "ETC",
            "切符",
            "定期",
            "Suica",
            "Pasmo",
            "ICOCA",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.ENTERTAINMENT,
        keywords=(
            "接待",
            "会食",
            "飲み会",
            "宴会",
            "懇親会",
            "ゴルフ",
            "贈答",
            "ギフト",
            "祝儀",
            "香典",
            "交際費",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.SUPPLIES,
        keywords=(
            "文具",
            "事務用品",
            "消耗品",
            "コピー用紙",
            "インク",
            "トナー",
            "ボールペン",
            "ノート",
            "ファイル",
            "封筒",
            "ハサミ",
            "のり",
            "テープ",
        ),
        weight=1.2,
    ),
    CategoryRule(
        category=AccountCategory.COMMUNICATION,
        keywords=(
            "通信",
            "電話",
            "携帯",
            "スマホ",
            "インターネット",
            "プロバイダ",
            "Wi-Fi",
            "wifi",
            "回線",
            "ドコモ",
            "au",
            "ソフトバンク",
            "楽天モバイル",
        ),
        weight=1.3,
    ),
    CategoryRule(
        category=AccountCategory.UTILITIES,
        keywords=(
            "電気",
            "ガス",
            "水道",
            "水道光熱費",
            "電力",
            "都市ガス",
            "プロパンガス",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.RENT,
        keywords=(
            "家賃",
            "地代",
            "賃貸",
            "駐車場代",
            "管理費",
            "共益費",
            "敷金",
            "礼金",
            "更新料",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.SALARY,
        keywords=(
            "給与",
            "給料",
            "賞与",
            "ボーナス",
            "手当",
            "残業代",
            "交通費支給",
            "社会保険",
            "雇用保険",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.OUTSOURCING,
        keywords=(
            "外注",
            "委託",
            "業務委託",
            "フリーランス",
            "請負",
            "アウトソーシング",
        ),
        weight=1.3,
    ),
    CategoryRule(
        category=AccountCategory.ADVERTISING,
        keywords=(
            "広告",
            "宣伝",
            "広告宣伝費",
            "チラシ",
            "ポスター",
            "Web広告",
            "リスティング",
            "SEO",
            "SNS広告",
        ),
        weight=1.3,
    ),
    CategoryRule(
        category=AccountCategory.REPAIR,
        keywords=(
            "修繕",
            "修理",
            "メンテナンス",
            "点検",
            "交換",
            "工事",
            "リフォーム",
            "塗装",
        ),
        weight=1.2,
    ),
    CategoryRule(
        category=AccountCategory.INSURANCE,
        keywords=(
            "保険",
            "生命保険",
            "損害保険",
            "火災保険",
            "自賠責",
            "任意保険",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.TAXES,
        keywords=(
            "税金",
            "税",
            "法人税",
            "住民税",
            "事業税",
            "固定資産税",
            "自動車税",
            "印紙税",
            "登録免許税",
        ),
        weight=1.5,
    ),
    CategoryRule(
        category=AccountCategory.DEPRECIATION,
        keywords=(
            "減価償却",
            "償却",
            "資産",
            "固定資産",
        ),
        weight=1.3,
    ),
)


class KeywordMatcher:
    """Keyword-based category matching.

    Single responsibility: Match text against keyword rules.
    """

    def __init__(self, rules: tuple[CategoryRule, ...] = DEFAULT_CATEGORY_RULES) -> None:
        """Initialize keyword matcher.

        Args:
            rules: Category rules to use for matching.
        """
        self._rules = rules
        # Pre-compile regex patterns for efficiency
        # For Japanese text, word boundaries (\b) don't work well
        # Use simple escaped keyword matching instead
        self._compiled_rules = [
            (rule.category, tuple(re.compile(re.escape(kw), re.IGNORECASE) for kw in rule.keywords), rule.weight)
            for rule in rules
        ]

    def match(self, text: str) -> list[tuple[AccountCategory, float]]:
        """Match text against category rules.

        Args:
            text: Text to analyze (store name, OCR text, etc.).

        Returns:
            List of (category, score) tuples sorted by score descending.
        """
        if not text or not text.strip():
            return []

        scores: dict[AccountCategory, float] = {}

        for category, patterns, weight in self._compiled_rules:
            matches = sum(1 for pattern in patterns if pattern.search(text))
            if matches > 0:
                # Score based on number of matches and rule weight
                score = min(matches * 0.3 * weight, 1.0)
                if category in scores:
                    scores[category] = max(scores[category], score)
                else:
                    scores[category] = score

        # Sort by score descending
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class CategoryClassifier:
    """Category classification service combining rules and AI.

    Implements RULE-BE-005: Category classification logic.
    Single responsibility: Determine account category for receipts.
    """

    def __init__(
        self,
        ai_service: Optional[AIAnalysisService] = None,
        keyword_matcher: Optional[KeywordMatcher] = None,
        use_ai: bool = True,
    ) -> None:
        """Initialize category classifier.

        Args:
            ai_service: AI analysis service for AI-based classification.
            keyword_matcher: Keyword matcher for rule-based classification.
            use_ai: Whether to use AI classification (fallback to rules if False).
        """
        self._ai_service = ai_service
        self._keyword_matcher = keyword_matcher or KeywordMatcher()
        self._use_ai = use_ai and ai_service is not None
        self._settings = get_settings()

        logger.info(
            "Category classifier initialized",
            extra={
                "use_ai": self._use_ai,
                "rules_count": len(self._keyword_matcher._rules),
            },
        )

    def classify_by_keywords(
        self,
        store_name: Optional[str],
        ocr_text: str,
        total_amount: Optional[int] = None,
    ) -> tuple[AccountCategory, float]:
        """Classify category using keyword matching.

        Args:
            store_name: Store/merchant name.
            ocr_text: Full OCR text from receipt.
            total_amount: Total amount (optional, for amount-based hints).

        Returns:
            Tuple of (category, confidence).
        """
        # Combine store name and OCR text for matching
        combined_text = " ".join(filter(None, [store_name, ocr_text]))

        matches = self._keyword_matcher.match(combined_text)

        if not matches:
            logger.debug("No keyword matches found, defaulting to その他")
            return AccountCategory.OTHER, 0.1

        best_category, best_score = matches[0]

        # Boost confidence if amount is typical for category
        if total_amount is not None:
            best_score = self._adjust_confidence_by_amount(best_category, best_score, total_amount)

        logger.debug(
            "Keyword classification result",
            extra={
                "category": best_category.value,
                "confidence": best_score,
                "matches_count": len(matches),
            },
        )

        return best_category, best_score

    def _adjust_confidence_by_amount(
        self, category: AccountCategory, confidence: float, amount: int
    ) -> float:
        """Adjust confidence based on amount typicality.

        Args:
            category: Classified category.
            confidence: Current confidence.
            amount: Total amount in yen.

        Returns:
            Adjusted confidence.
        """
        # Simple heuristics for amount ranges
        amount_ranges = {
            AccountCategory.TRAVEL_EXPENSE: (100, 50000),
            AccountCategory.ENTERTAINMENT: (1000, 100000),
            AccountCategory.SUPPLIES: (100, 20000),
            AccountCategory.COMMUNICATION: (1000, 50000),
            AccountCategory.UTILITIES: (2000, 100000),
            AccountCategory.RENT: (30000, 500000),
            AccountCategory.SALARY: (100000, 2000000),
            AccountCategory.OUTSOURCING: (5000, 1000000),
            AccountCategory.ADVERTISING: (1000, 1000000),
            AccountCategory.REPAIR: (1000, 500000),
            AccountCategory.INSURANCE: (5000, 500000),
            AccountCategory.TAXES: (1000, 2000000),
            AccountCategory.DEPRECIATION: (10000, 5000000),
        }

        if category in amount_ranges:
            min_amt, max_amt = amount_ranges[category]
            if min_amt <= amount <= max_amt:
                return min(confidence + 0.1, 1.0)
            elif amount < min_amt * 0.1 or amount > max_amt * 10:
                return max(confidence - 0.1, 0.0)

        return confidence

    async def classify_with_ai(
        self,
        store_name: Optional[str],
        total_amount: Optional[int],
        ocr_text: str,
    ) -> tuple[AccountCategory, float]:
        """Classify category using AI analysis.

        Args:
            store_name: Store/merchant name.
            total_amount: Total amount.
            ocr_text: Full OCR text.

        Returns:
            Tuple of (category, confidence).
        """
        if not self._use_ai or self._ai_service is None:
            logger.warning("AI classification requested but AI service unavailable")
            return self.classify_by_keywords(store_name, ocr_text, total_amount)

        try:
            category_str, confidence = await self._ai_service.classify_category(
                store_name, total_amount, ocr_text
            )
            category = AccountCategory(category_str)
            return category, confidence
        except Exception as e:
            logger.error(
                "AI category classification failed, falling back to keywords",
                extra={"error": str(e)},
            )
            return self.classify_by_keywords(store_name, ocr_text, total_amount)

    async def classify(
        self,
        store_name: Optional[str],
        total_amount: Optional[int],
        ocr_text: str,
        ai_category: Optional[str] = None,
        ai_confidence: float = 0.0,
    ) -> tuple[AccountCategory, float]:
        """Classify category using best available method.

        Priority:
        1. AI-provided category (if confidence is high)
        2. AI classification
        3. Keyword-based classification

        Args:
            store_name: Store/merchant name.
            total_amount: Total amount.
            ocr_text: Full OCR text.
            ai_category: Category from AI analysis (optional).
            ai_confidence: Confidence of AI category (optional).

        Returns:
            Tuple of (category, confidence).
        """
        # If AI already provided a high-confidence category, use it
        if ai_category and ai_confidence >= 0.7:
            try:
                category = AccountCategory(ai_category)
                logger.info(
                    "Using AI-provided category",
                    extra={"category": category.value, "confidence": ai_confidence},
                )
                return category, ai_confidence
            except ValueError:
                logger.warning("Invalid AI category, falling back", extra={"category": ai_category})

        # Try AI classification if enabled
        if self._use_ai:
            category, confidence = await self.classify_with_ai(
                store_name, total_amount, ocr_text
            )
            if confidence >= 0.5:
                return category, confidence

        # Fallback to keyword matching
        return self.classify_by_keywords(store_name, ocr_text, total_amount)

    def get_category_hierarchy(self, category: AccountCategory) -> list[AccountCategory]:
        """Get category hierarchy (parent categories).

        For this system, categories are flat (no hierarchy), but this method
        provides extensibility for future hierarchical categories.

        Args:
            category: The category.

        Returns:
            List containing the category itself (flat hierarchy).
        """
        return [category]


async def get_category_classifier() -> CategoryClassifier:
    """Get category classifier instance (dependency injection helper).

    Returns:
        CategoryClassifier instance.
    """
    ai_service = await get_ai_analysis_service()
    return CategoryClassifier(ai_service=ai_service)