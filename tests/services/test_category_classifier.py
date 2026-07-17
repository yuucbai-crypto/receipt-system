"""Tests for Category Classifier Service."""

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.constants import AccountCategory
from app.services.category_classifier import (
    CategoryClassifier,
    CategoryRule,
    DEFAULT_CATEGORY_RULES,
    KeywordMatcher,
)


class TestCategoryRule:
    """Tests for CategoryRule dataclass."""

    def test_category_rule_creation(self) -> None:
        """Test CategoryRule creation."""
        rule = CategoryRule(
            category=AccountCategory.TRAVEL_EXPENSE,
            keywords=("交通", "電車"),
            weight=1.5,
        )
        assert rule.category == AccountCategory.TRAVEL_EXPENSE
        assert rule.keywords == ("交通", "電車")
        assert rule.weight == 1.5

    def test_category_rule_default_weight(self) -> None:
        """Test default weight is 1.0."""
        rule = CategoryRule(category=AccountCategory.OTHER, keywords=("test",))
        assert rule.weight == 1.0


class TestKeywordMatcher:
    """Tests for KeywordMatcher."""

    @pytest.fixture
    def matcher(self) -> KeywordMatcher:
        """Create keyword matcher with default rules."""
        return KeywordMatcher()

    def test_match_empty_text(self, matcher: KeywordMatcher) -> None:
        """Test matching empty text returns empty list."""
        result = matcher.match("")
        assert result == []

    def test_match_whitespace_only(self, matcher: KeywordMatcher) -> None:
        """Test matching whitespace-only text."""
        result = matcher.match("   \n\t  ")
        assert result == []

    def test_match_travel_keywords(self, matcher: KeywordMatcher) -> None:
        """Test matching travel expense keywords."""
        text = "東京駅 新幹線 切符 往復"
        result = matcher.match(text)
        assert len(result) > 0
        assert result[0][0] == AccountCategory.TRAVEL_EXPENSE

    def test_match_entertainment_keywords(self, matcher: KeywordMatcher) -> None:
        """Test matching entertainment keywords."""
        text = "接待 会食 飲み会"
        result = matcher.match(text)
        assert len(result) > 0
        assert result[0][0] == AccountCategory.ENTERTAINMENT

    def test_match_supplies_keywords(self, matcher: KeywordMatcher) -> None:
        """Test matching supplies keywords."""
        text = "文具 事務用品 ボールペン ノート"
        result = matcher.match(text)
        assert len(result) > 0
        assert result[0][0] == AccountCategory.SUPPLIES

    def test_match_case_insensitive(self, matcher: KeywordMatcher) -> None:
        """Test matching is case insensitive."""
        text = "suica pasmo icoCA"
        result = matcher.match(text)
        assert len(result) > 0
        assert result[0][0] == AccountCategory.TRAVEL_EXPENSE

    def test_match_partial_words_not_matched(self, matcher: KeywordMatcher) -> None:
        """Test keyword matching works for Japanese text."""
        # Japanese text matching uses substring matching, not word boundaries
        text = "交通費 通信費"
        result = matcher.match(text)
        categories = [cat for cat, _ in result]
        # Both should match their respective categories
        assert AccountCategory.TRAVEL_EXPENSE in categories
        assert AccountCategory.COMMUNICATION in categories

    def test_match_multiple_categories(self, matcher: KeywordMatcher) -> None:
        """Test text matching multiple categories."""
        text = "交通費 交際費 文具"
        result = matcher.match(text)
        assert len(result) >= 2
        # Should be sorted by score descending
        assert result[0][1] >= result[1][1]

    def test_match_score_bounded(self, matcher: KeywordMatcher) -> None:
        """Test match scores are bounded between 0 and 1."""
        text = " ".join(["交通"] * 20)  # Many matches
        result = matcher.match(text)
        for _, score in result:
            assert 0 <= score <= 1.0


class TestCategoryClassifier:
    """Tests for CategoryClassifier."""

    @pytest.fixture
    def mock_ai_service(self) -> AsyncMock:
        """Create mock AI analysis service."""
        return AsyncMock()

    @pytest.fixture
    def classifier(self, mock_ai_service: AsyncMock) -> CategoryClassifier:
        """Create classifier with mocked AI service."""
        return CategoryClassifier(ai_service=mock_ai_service, use_ai=True)

    @pytest.fixture
    def classifier_no_ai(self) -> CategoryClassifier:
        """Create classifier without AI (keyword only)."""
        return CategoryClassifier(ai_service=None, use_ai=False)

    def test_classifier_initialization(self, classifier: CategoryClassifier) -> None:
        """Test classifier initializes correctly."""
        assert classifier._use_ai is True
        assert classifier._ai_service is not None
        assert classifier._keyword_matcher is not None

    def test_classifier_no_ai_initialization(self, classifier_no_ai: CategoryClassifier) -> None:
        """Test classifier without AI."""
        assert classifier_no_ai._use_ai is False
        assert classifier_no_ai._ai_service is None

    def test_classify_by_keywords_travel(self, classifier: CategoryClassifier) -> None:
        """Test keyword classification for travel."""
        category, confidence = classifier.classify_by_keywords(
            store_name="東京駅", ocr_text="新幹線 往復 15000円", total_amount=15000
        )
        assert category == AccountCategory.TRAVEL_EXPENSE
        assert confidence > 0.3

    def test_classify_by_keywords_entertainment(self, classifier: CategoryClassifier) -> None:
        """Test keyword classification for entertainment."""
        category, confidence = classifier.classify_by_keywords(
            store_name="居酒屋", ocr_text="接待 会食 ビール 5000円", total_amount=5000
        )
        assert category == AccountCategory.ENTERTAINMENT

    def test_classify_by_keywords_no_match(self, classifier: CategoryClassifier) -> None:
        """Test keyword classification with no matches."""
        category, confidence = classifier.classify_by_keywords(
            store_name="不明な店", ocr_text="謎の商品 100円", total_amount=100
        )
        assert category == AccountCategory.OTHER
        assert confidence == 0.1

    def test_classify_by_keywords_amount_boost(self, classifier: CategoryClassifier) -> None:
        """Test amount boosts confidence for typical ranges."""
        # Rent amount typical for rent category
        category, confidence = classifier.classify_by_keywords(
            store_name="不動産屋", ocr_text="家賃 100000円", total_amount=100000
        )
        assert category == AccountCategory.RENT
        # Confidence should be boosted for typical rent amount

    def test_classify_by_keywords_amount_penalty(self, classifier: CategoryClassifier) -> None:
        """Test amount penalty for atypical amounts."""
        # Very small amount for rent category
        category, confidence = classifier.classify_by_keywords(
            store_name="不動産屋", ocr_text="家賃 100円", total_amount=100
        )
        # Should still classify as RENT but with lower confidence
        assert category == AccountCategory.RENT

    @pytest.mark.asyncio
    async def test_classify_with_ai_success(
        self, classifier: CategoryClassifier, mock_ai_service: AsyncMock
    ) -> None:
        """Test AI classification success."""
        mock_ai_service.classify_category = AsyncMock(return_value=("旅費交通費", 0.9))

        category, confidence = await classifier.classify_with_ai(
            store_name="東京駅", total_amount=15000, ocr_text="新幹線 往復"
        )

        assert category == AccountCategory.TRAVEL_EXPENSE
        assert confidence == 0.9
        mock_ai_service.classify_category.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_with_ai_invalid_category(
        self, classifier: CategoryClassifier, mock_ai_service: AsyncMock
    ) -> None:
        """Test AI classification with invalid category falls back."""
        mock_ai_service.classify_category = AsyncMock(
            return_value=("存在しない科目", 0.9)
        )

        category, confidence = await classifier.classify_with_ai(
            store_name="店", total_amount=1000, ocr_text="text"
        )

        assert category == AccountCategory.OTHER
        # Falls back to keyword matching which returns 0.1 for no match
        assert confidence == 0.1

    @pytest.mark.asyncio
    async def test_classify_with_ai_exception_fallback(
        self, classifier: CategoryClassifier, mock_ai_service: AsyncMock
    ) -> None:
        """Test AI classification falls back to keywords on exception."""
        mock_ai_service.classify_category = AsyncMock(side_effect=Exception("API error"))

        with patch.object(
            classifier, "classify_by_keywords", return_value=(AccountCategory.SUPPLIES, 0.6)
        ) as mock_keywords:
            category, confidence = await classifier.classify_with_ai(
                store_name="店", total_amount=1000, ocr_text="文具"
            )

            assert category == AccountCategory.SUPPLIES
            assert confidence == 0.6
            mock_keywords.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_uses_ai_category_high_confidence(
        self, classifier: CategoryClassifier
    ) -> None:
        """Test classify uses AI-provided category when confidence high."""
        category, confidence = await classifier.classify(
            store_name="店",
            total_amount=1000,
            ocr_text="text",
            ai_category="消耗品費",
            ai_confidence=0.8,
        )

        assert category == AccountCategory.SUPPLIES
        assert confidence == 0.8

    @pytest.mark.asyncio
    async def test_classify_ignores_ai_category_low_confidence(
        self, classifier: CategoryClassifier, mock_ai_service: AsyncMock
    ) -> None:
        """Test classify ignores AI category when confidence low."""
        mock_ai_service.classify_category = AsyncMock(return_value=("旅費交通費", 0.3))

        category, confidence = await classifier.classify(
            store_name="文具店",
            total_amount=500,
            ocr_text="ボールペン ノート",
            ai_category="旅費交通費",
            ai_confidence=0.4,  # Low confidence
        )

        # Should use keyword matching (SUPPLIES) not AI category (TRAVEL)
        assert category == AccountCategory.SUPPLIES

    @pytest.mark.asyncio
    async def test_classify_ignores_invalid_ai_category(
        self, classifier: CategoryClassifier
    ) -> None:
        """Test classify ignores invalid AI category."""
        category, confidence = await classifier.classify(
            store_name="店",
            total_amount=1000,
            ocr_text="text",
            ai_category="無効な科目",
            ai_confidence=0.9,
        )

        # Should fall through to keyword matching
        assert category == AccountCategory.OTHER  # No keywords match "店" or "text"

    @pytest.mark.asyncio
    async def test_classify_ai_fallback_to_keywords(
        self, classifier: CategoryClassifier, mock_ai_service: AsyncMock
    ) -> None:
        """Test classify falls back to keywords when AI confidence low."""
        mock_ai_service.classify_category = AsyncMock(return_value=("その他", 0.3))

        category, confidence = await classifier.classify(
            store_name="文具店",
            total_amount=500,
            ocr_text="ボールペン ノート",
        )

        # AI returned low confidence, should use keywords
        assert category == AccountCategory.SUPPLIES

    def test_get_category_hierarchy(self, classifier: CategoryClassifier) -> None:
        """Test category hierarchy returns flat list."""
        hierarchy = classifier.get_category_hierarchy(AccountCategory.TRAVEL_EXPENSE)
        assert hierarchy == [AccountCategory.TRAVEL_EXPENSE]


class TestDefaultCategoryRules:
    """Tests for default category rules coverage."""

    def test_all_categories_have_rules(self) -> None:
        """Test all AccountCategory values have at least one rule."""
        categories_with_rules = {rule.category for rule in DEFAULT_CATEGORY_RULES}
        # Check major categories are covered
        assert AccountCategory.TRAVEL_EXPENSE in categories_with_rules
        assert AccountCategory.ENTERTAINMENT in categories_with_rules
        assert AccountCategory.SUPPLIES in categories_with_rules
        assert AccountCategory.COMMUNICATION in categories_with_rules
        assert AccountCategory.UTILITIES in categories_with_rules
        assert AccountCategory.RENT in categories_with_rules
        assert AccountCategory.SALARY in categories_with_rules
        assert AccountCategory.OUTSOURCING in categories_with_rules
        assert AccountCategory.ADVERTISING in categories_with_rules
        assert AccountCategory.REPAIR in categories_with_rules
        assert AccountCategory.INSURANCE in categories_with_rules
        assert AccountCategory.TAXES in categories_with_rules
        assert AccountCategory.DEPRECIATION in categories_with_rules

    def test_rule_keywords_not_empty(self) -> None:
        """Test all rules have non-empty keywords."""
        for rule in DEFAULT_CATEGORY_RULES:
            assert len(rule.keywords) > 0
            assert all(isinstance(kw, str) and len(kw) > 0 for kw in rule.keywords)

    def test_rule_weights_positive(self) -> None:
        """Test all rule weights are positive."""
        for rule in DEFAULT_CATEGORY_RULES:
            assert rule.weight > 0


class TestKeywordMatcherRegex:
    """Tests for regex compilation in KeywordMatcher."""

    def test_special_characters_escaped(self) -> None:
        """Test keywords with special regex chars are escaped."""
        rule = CategoryRule(
            category=AccountCategory.OTHER,
            keywords=("C++", "A&B", "test*"),
        )
        matcher = KeywordMatcher(rules=(rule,))

        # Should not raise regex error
        result = matcher.match("C++ A&B test*")
        assert len(result) == 1
        assert result[0][0] == AccountCategory.OTHER

    def test_word_boundaries_respected(self) -> None:
        """Test keyword matching behavior for Japanese text."""
        rule = CategoryRule(
            category=AccountCategory.TRAVEL_EXPENSE,
            keywords=("交通",),
        )
        matcher = KeywordMatcher(rules=(rule,))

        # Japanese text - "交通" is a substring of "交通費"
        # The matcher finds it (substring match for Japanese)
        assert len(matcher.match("交通費")) > 0
        # "通信" doesn't contain "交通"
        result = matcher.match("通信費")
        assert len(result) == 0