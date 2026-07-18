"""Duplicate Check Service for receipt duplicate detection.

Implements RULE-BE-006: Composite score calculation for duplicate detection.
Implements RULE-FLOW-001-7: Duplicate candidate check in receipt processing flow.
Implements RULE-ERR-009: Handle insufficient comparison data gracefully.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import ReceiptStatus
from app.models.duplicate_check import DuplicateCheckStatus
from app.core.logging import get_logger
from app.models.duplicate_check import DuplicateCheck
from app.models.receipt import Receipt

if TYPE_CHECKING:
    from app.models.receipt import Receipt

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DuplicateScoreComponents:
    """Individual score components for duplicate detection.

    Attributes:
        store_name_score: Store name similarity (0.0-1.0).
        amount_score: Amount similarity (0.0-1.0).
        date_score: Date similarity (0.0-1.0).
        metadata_score: Metadata similarity (0.0-1.0).
        image_hash_score: Image hash similarity (0.0-1.0).
        ocr_similarity_score: OCR text similarity (0.0-1.0).
        composite_score: Weighted composite score (0.0-1.0).
        has_sufficient_data: Whether sufficient data exists for comparison.
    """

    store_name_score: float | None
    amount_score: float | None
    date_score: float | None
    metadata_score: float | None
    image_hash_score: float | None
    ocr_similarity_score: float | None
    composite_score: float
    has_sufficient_data: bool


@dataclass(frozen=True, slots=True)
class DuplicateCheckResult:
    """Result of duplicate check operation.

    Attributes:
        is_duplicate: Whether duplicate was detected (score >= threshold).
        composite_score: Composite similarity score.
        score_components: Individual score components.
        duplicate_check_id: ID of saved DuplicateCheck record (if saved).
        error: Error message if check failed.
    """

    is_duplicate: bool
    composite_score: float
    score_components: DuplicateScoreComponents
    duplicate_check_id: int | None = None
    error: str | None = None


# Default weights for composite score calculation (RULE-BE-006)
DEFAULT_WEIGHTS = {
    "store_name": 0.25,
    "amount": 0.20,
    "date": 0.15,
    "metadata": 0.10,
    "image_hash": 0.15,
    "ocr_similarity": 0.15,
}

# Minimum required fields for meaningful comparison (RULE-ERR-009)
MIN_REQUIRED_FIELDS = 2

# Default duplicate threshold (RULE-BE-006)
DEFAULT_DUPLICATE_THRESHOLD = 0.85


class DuplicateCheckService:
    """Service for detecting duplicate receipts using composite scoring.

    Single responsibility: Compare receipts and compute duplicate scores.
    Uses existing DuplicateCheck model for persistence.
    """

    def __init__(
        self,
        session,
        weights: dict[str, float] | None = None,
        duplicate_threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
    ) -> None:
        """Initialize duplicate check service.

        Args:
            session: Database session.
            weights: Custom weights for score components (must sum to 1.0).
            duplicate_threshold: Threshold for duplicate detection (0.0-1.0).
        """
        self._session = session
        self._weights = weights or DEFAULT_WEIGHTS
        self._duplicate_threshold = duplicate_threshold
        self._settings = get_settings()

        # Validate weights sum to 1.0
        total_weight = sum(self._weights.values())
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(
                "Weights do not sum to 1.0, normalizing",
                extra={"weights": self._weights, "sum": total_weight},
            )
            self._weights = {k: v / total_weight for k, v in self._weights.items()}

    def _compute_store_name_score(self, store1: str | None, store2: str | None) -> float | None:
        """Compute store name similarity score.

        Uses SequenceMatcher for fuzzy string matching.

        Args:
            store1: First store name.
            store2: Second store name.

        Returns:
            Similarity score (0.0-1.0) or None if either is missing.
        """
        if not store1 or not store2:
            return None

        # Normalize: lowercase, strip whitespace
        s1 = store1.strip().lower()
        s2 = store2.strip().lower()

        if s1 == s2:
            return 1.0

        return SequenceMatcher(None, s1, s2).ratio()

    def _compute_amount_score(self, amount1: int | None, amount2: int | None) -> float | None:
        """Compute amount similarity score.

        Exact match = 1.0, close amounts get partial score.

        Args:
            amount1: First amount in yen.
            amount2: Second amount in yen.

        Returns:
            Similarity score (0.0-1.0) or None if either is missing.
        """
        if amount1 is None or amount2 is None:
            return None

        if amount1 == amount2:
            return 1.0

        # Calculate relative difference
        max_amt = max(amount1, amount2)
        min_amt = min(amount1, amount2)
        if max_amt == 0:
            return 1.0 if min_amt == 0 else 0.0

        diff_ratio = (max_amt - min_amt) / max_amt
        # Score decreases as difference increases
        return max(0.0, 1.0 - diff_ratio)

    def _compute_date_score(
        self, date1: datetime | None, date2: datetime | None
    ) -> float | None:
        """Compute date similarity score.

        Exact match = 1.0, same day = 1.0, within 1 day = 0.9, within 7 days = 0.5.

        Args:
            date1: First receipt date.
            date2: Second receipt date.

        Returns:
            Similarity score (0.0-1.0) or None if either is missing.
        """
        if date1 is None or date2 is None:
            return None

        # Compare dates only (ignore time)
        d1 = date1.date() if hasattr(date1, "date") else date1
        d2 = date2.date() if hasattr(date2, "date") else date2

        if d1 == d2:
            return 1.0

        delta_days = abs((d1 - d2).days)

        if delta_days == 0:
            return 1.0
        elif delta_days == 1:
            return 0.9
        elif delta_days <= 3:
            return 0.7
        elif delta_days <= 7:
            return 0.5
        elif delta_days <= 30:
            return 0.3
        else:
            return 0.1

    def _compute_metadata_score(
        self,
        receipt1: "Receipt",
        receipt2: "Receipt",
    ) -> float | None:
        """Compute metadata similarity score.

        Compares: tax_amount, currency, category, tags.

        Args:
            receipt1: First receipt.
            receipt2: Second receipt.

        Returns:
            Similarity score (0.0-1.0) or None if insufficient data.
        """
        scores = []

        # Tax amount comparison
        if receipt1.tax_amount is not None and receipt2.tax_amount is not None:
            if receipt1.tax_amount == receipt2.tax_amount:
                scores.append(1.0)
            else:
                max_tax = max(receipt1.tax_amount, receipt2.tax_amount)
                min_tax = min(receipt1.tax_amount, receipt2.tax_amount)
                if max_tax > 0:
                    scores.append(1.0 - (max_tax - min_tax) / max_tax)
                else:
                    scores.append(1.0)

        # Currency comparison
        if receipt1.currency and receipt2.currency:
            scores.append(1.0 if receipt1.currency == receipt2.currency else 0.0)

        # Category comparison
        if receipt1.category_id is not None and receipt2.category_id is not None:
            scores.append(1.0 if receipt1.category_id == receipt2.category_id else 0.0)

        # Tags comparison (Jaccard similarity)
        tags1 = set(receipt1.tags) if receipt1.tags else set()
        tags2 = set(receipt2.tags) if receipt2.tags else set()
        if tags1 or tags2:
            intersection = len(tags1 & tags2)
            union = len(tags1 | tags2)
            scores.append(intersection / union if union > 0 else 0.0)

        if not scores:
            return None

        return sum(scores) / len(scores)

    def _compute_image_hash_score(
        self, hash1: str | None, hash2: str | None
    ) -> float | None:
        """Compute image hash similarity score.

        Uses Hamming distance on hex hashes (SHA-256).

        Args:
            hash1: First image hash (hex string).
            hash2: Second image hash (hex string).

        Returns:
            Similarity score (0.0-1.0) or None if either is missing.
        """
        if not hash1 or not hash2:
            return None

        if hash1 == hash2:
            return 1.0

        # Compute Hamming distance
        try:
            # Convert hex to binary
            b1 = bin(int(hash1, 16))[2:].zfill(256)
            b2 = bin(int(hash2, 16))[2:].zfill(256)
            distance = sum(c1 != c2 for c1, c2 in zip(b1, b2, strict=False))
            # Normalize: 0 distance = 1.0, max distance (256) = 0.0
            return max(0.0, 1.0 - (distance / 256.0))
        except ValueError:
            logger.warning("Invalid hash format for comparison")
            return None

    def _compute_ocr_similarity_score(
        self, ocr1: str | None, ocr2: str | None
    ) -> float | None:
        """Compute OCR text similarity score.

        Uses SequenceMatcher for text similarity.

        Args:
            ocr1: First OCR text.
            ocr2: Second OCR text.

        Returns:
            Similarity score (0.0-1.0) or None if either is missing.
        """
        if not ocr1 or not ocr2:
            return None

        return SequenceMatcher(None, ocr1.strip(), ocr2.strip()).ratio()

    def _compute_composite_score(
        self,
        components: DuplicateScoreComponents,
    ) -> float:
        """Compute weighted composite score.

        Args:
            components: Individual score components.

        Returns:
            Weighted composite score.
        """
        score = 0.0
        total_weight = 0.0

        # Store name
        if components.store_name_score is not None:
            score += components.store_name_score * self._weights.get("store_name", 0.0)
            total_weight += self._weights.get("store_name", 0.0)

        # Amount
        if components.amount_score is not None:
            score += components.amount_score * self._weights.get("amount", 0.0)
            total_weight += self._weights.get("amount", 0.0)

        # Date
        if components.date_score is not None:
            score += components.date_score * self._weights.get("date", 0.0)
            total_weight += self._weights.get("date", 0.0)

        # Metadata
        if components.metadata_score is not None:
            score += components.metadata_score * self._weights.get("metadata", 0.0)
            total_weight += self._weights.get("metadata", 0.0)

        # Image hash
        if components.image_hash_score is not None:
            score += components.image_hash_score * self._weights.get("image_hash", 0.0)
            total_weight += self._weights.get("image_hash", 0.0)

        # OCR similarity
        if components.ocr_similarity_score is not None:
            score += components.ocr_similarity_score * self._weights.get("ocr_similarity", 0.0)
            total_weight += self._weights.get("ocr_similarity", 0.0)

        # Normalize by actual weights used (in case some components are None)
        if total_weight > 0:
            return score / total_weight
        return 0.0

    def _check_sufficient_data(self, components: DuplicateScoreComponents) -> bool:
        """Check if sufficient data exists for meaningful comparison.

        RULE-ERR-009: If comparison data is insufficient, treat as no duplicates.

        Args:
            components: Score components.

        Returns:
            True if sufficient data exists.
        """
        available = sum(
            1
            for v in [
                components.store_name_score,
                components.amount_score,
                components.date_score,
                components.metadata_score,
                components.image_hash_score,
                components.ocr_similarity_score,
            ]
            if v is not None
        )
        return available >= MIN_REQUIRED_FIELDS

    def _has_sufficient_data_for_comparison(
        self, source: "Receipt", target: "Receipt"
    ) -> bool:
        """Check if two receipts have sufficient data for comparison.
        
        RULE-ERR-009: Check before computing scores to avoid unnecessary work.
        
        Args:
            source: Source receipt.
            target: Target receipt.
            
        Returns:
            True if at least MIN_REQUIRED_FIELDS are available on both receipts.
        """
        available = 0
        # Store name
        if source.store_name and target.store_name:
            available += 1
        # Amount
        if source.total_amount is not None and target.total_amount is not None:
            available += 1
        # Date
        if source.receipt_date is not None and target.receipt_date is not None:
            available += 1
        # Metadata (tax_amount, currency, category_id, tags)
        meta_available = 0
        if source.tax_amount is not None and target.tax_amount is not None:
            meta_available += 1
        if source.currency and target.currency:
            meta_available += 1
        if source.category_id is not None and target.category_id is not None:
            meta_available += 1
        if source.tags and target.tags:
            meta_available += 1
        if meta_available > 0:
            available += 1
        # Image hash
        if source.image_hash and target.image_hash:
            available += 1
        # OCR text
        if source.ocr_text and target.ocr_text:
            available += 1
        return available >= MIN_REQUIRED_FIELDS

    def is_duplicate(self, composite_score: float) -> bool:
        """Determine if composite score indicates a duplicate.

        Args:
            composite_score: Composite similarity score.

        Returns:
            True if duplicate (score >= threshold).
        """
        return composite_score >= self._duplicate_threshold

    async def check_duplicate(
        self,
        source_receipt: "Receipt",
        target_receipt: "Receipt",
        save_result: bool = True,
    ) -> DuplicateCheckResult:
        """Check if two receipts are duplicates.

        Implements RULE-FLOW-001-7: Duplicate candidate check.
        Implements RULE-ERR-009: Insufficient data handling.

        Args:
            source_receipt: Newly processed receipt.
            target_receipt: Existing receipt to compare against.
            save_result: Whether to save DuplicateCheck record.

        Returns:
            DuplicateCheckResult with scores and duplicate decision.
        """
        logger.info(
            "Checking duplicate",
            extra={
                "source_id": source_receipt.id,
                "target_id": target_receipt.id,
            },
        )

        # Check sufficient data FIRST (RULE-ERR-009)
        # Avoid computing scores if data is insufficient
        if not self._has_sufficient_data_for_comparison(source_receipt, target_receipt):
            logger.info(
                "Insufficient data for duplicate comparison, treating as no duplicate",
                extra={
                    "source_id": source_receipt.id,
                    "target_id": target_receipt.id,
                },
            )
            empty_components = DuplicateScoreComponents(
                store_name_score=None,
                amount_score=None,
                date_score=None,
                metadata_score=None,
                image_hash_score=None,
                ocr_similarity_score=None,
                composite_score=0.0,
                has_sufficient_data=False,
            )
            return DuplicateCheckResult(
                is_duplicate=False,
                composite_score=0.0,
                score_components=empty_components,
            )

        # Compute individual scores (only reached if sufficient data exists)
        store_name_score = self._compute_store_name_score(
            source_receipt.store_name, target_receipt.store_name
        )
        amount_score = self._compute_amount_score(
            source_receipt.total_amount, target_receipt.total_amount
        )
        date_score = self._compute_date_score(
            source_receipt.receipt_date, target_receipt.receipt_date
        )
        metadata_score = self._compute_metadata_score(source_receipt, target_receipt)
        image_hash_score = self._compute_image_hash_score(
            source_receipt.image_hash, target_receipt.image_hash
        )
        ocr_similarity_score = self._compute_ocr_similarity_score(
            source_receipt.ocr_text, target_receipt.ocr_text
        )

        components = DuplicateScoreComponents(
            store_name_score=store_name_score,
            amount_score=amount_score,
            date_score=date_score,
            metadata_score=metadata_score,
            image_hash_score=image_hash_score,
            ocr_similarity_score=ocr_similarity_score,
            composite_score=0.0,  # Will be computed
            has_sufficient_data=True,  # We already verified
        )

        # Compute composite score
        composite_score = self._compute_composite_score(components)
        is_duplicate = composite_score >= self._duplicate_threshold

        # Update components with computed values
        components = DuplicateScoreComponents(
            store_name_score=store_name_score,
            amount_score=amount_score,
            date_score=date_score,
            metadata_score=metadata_score,
            image_hash_score=image_hash_score,
            ocr_similarity_score=ocr_similarity_score,
            composite_score=composite_score,
            has_sufficient_data=True,
        )

        duplicate_check_id = None
        if save_result:
            duplicate_check = DuplicateCheck(
                source_receipt_id=source_receipt.id,
                target_receipt_id=target_receipt.id,
                store_name_score=store_name_score,
                amount_score=amount_score,
                date_score=date_score,
                metadata_score=metadata_score,
                image_hash_score=image_hash_score,
                ocr_similarity_score=ocr_similarity_score,
                composite_score=composite_score,
                duplicate_threshold=self._duplicate_threshold,
                is_duplicate=is_duplicate,
                status=(
                    DuplicateCheckStatus.HAS_DUPLICATES
                    if is_duplicate
                    else DuplicateCheckStatus.NO_DUPLICATES
                ),
                processing_started_at=datetime.now(timezone.utc),
                processing_completed_at=datetime.now(timezone.utc),
            )
            self._session.add(duplicate_check)
            await self._session.flush()
            duplicate_check_id = duplicate_check.id

            logger.info(
                "Duplicate check completed",
                extra={
                    "duplicate_check_id": duplicate_check_id,
                    "source_id": source_receipt.id,
                    "target_id": target_receipt.id,
                    "is_duplicate": is_duplicate,
                    "composite_score": composite_score,
                },
            )

        return DuplicateCheckResult(
            is_duplicate=is_duplicate,
            composite_score=composite_score,
            score_components=components,
            duplicate_check_id=duplicate_check_id,
        )

    async def find_potential_duplicates(
        self,
        source_receipt: "Receipt",
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[DuplicateCheckResult]:
        """Find potential duplicate receipts for a source receipt.

        Queries existing receipts and compares against the source.

        Args:
            source_receipt: Receipt to check for duplicates.
            limit: Maximum number of results.
            min_score: Minimum composite score to consider.

        Returns:
            List of DuplicateCheckResult sorted by composite score (descending).
        """
        # Query candidates: same date range, similar amount, or same store
        stmt = (
            select(Receipt)
            .where(Receipt.id != source_receipt.id)
            .where(Receipt.status.in_([ReceiptStatus.UNAPPROVED, ReceiptStatus.APPROVED]))
            .order_by(Receipt.receipt_date.desc().nullslast())
            .limit(limit * 3)  # Get more candidates for filtering
        )

        # Add amount filter if available
        if source_receipt.total_amount is not None:
            amount = source_receipt.total_amount
            margin = max(int(amount * 0.1), 100)  # 10% or 100 yen minimum
            stmt = stmt.where(
                Receipt.total_amount.between(amount - margin, amount + margin)
            )

        # Add date filter if available
        if source_receipt.receipt_date is not None:
            date = source_receipt.receipt_date
            stmt = stmt.where(
                Receipt.receipt_date.between(
                    date - timedelta(days=30), date + timedelta(days=30)
                )
            )

        result = await self._session.execute(stmt)
        candidates = result.scalars().all()

        # Score each candidate
        results = []
        for candidate in candidates:
            check_result = await self.check_duplicate(
                source_receipt, candidate, save_result=False
            )
            if check_result.score_components.has_sufficient_data:
                results.append(check_result)

        # Sort by composite score descending
        results.sort(key=lambda r: r.composite_score, reverse=True)

        return results[:limit]


async def get_duplicate_check_service(session) -> DuplicateCheckService:
    """Dependency injection helper for DuplicateCheckService.

    Args:
        session: Database session.

    Returns:
        DuplicateCheckService instance.
    """
    return DuplicateCheckService(session)