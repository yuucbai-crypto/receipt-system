"""Rejection Reason Service for storing receipt rejection reasons.

Implements RULE-BE-018: Rejection reason data persistence.
Implements RULE-FLOW-001-11: Rejection reason storage on rejection.
Implements RULE-GEN-020: Type hints on all Python code.
Implements RULE-GEN-021: Single responsibility principle.

Stores rejection data for future AI rule learning.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.receipt import Receipt, ReceiptStatus
from app.models.rejection_reason import RejectionReason

if TYPE_CHECKING:
    from app.models.receipt import Receipt

logger = get_logger(__name__)


class RejectionReasonCode(StrEnum):
    """Standardized rejection reason codes.

    These codes enable consistent categorization and future ML training.
    """

    # Quality issues
    POOR_IMAGE_QUALITY = "poor_image_quality"
    BLURRY_IMAGE = "blurry_image"
    LOW_RESOLUTION = "low_resolution"
    CUTOFF_CONTENT = "cutoff_content"
    WRONG_ORIENTATION = "wrong_orientation"

    # OCR/AI issues
    OCR_FAILED = "ocr_failed"
    OCR_LOW_CONFIDENCE = "ocr_low_confidence"
    AI_EXTRACTION_FAILED = "ai_extraction_failed"
    AI_LOW_CONFIDENCE = "ai_low_confidence"
    MISSING_CRITICAL_FIELDS = "missing_critical_fields"

    # Data issues
    DUPLICATE_RECEIPT = "duplicate_receipt"
    INVALID_DATE = "invalid_date"
    INVALID_AMOUNT = "invalid_amount"
    INVALID_STORE_NAME = "invalid_store_name"
    MISMATCHED_DATA = "mismatched_data"

    # Business rules
    NON_DEDUCTIBLE = "non_deductible"
    PERSONAL_EXPENSE = "personal_expense"
    OUT_OF_POLICY = "out_of_policy"
    EXCEEDS_LIMIT = "exceeds_limit"
    MISSING_APPROVAL = "missing_approval"

    # Other
    OTHER = "other"
    USER_CANCELLED = "user_cancelled"


class RejectionCategory(StrEnum):
    """High-level rejection categories."""

    IMAGE_QUALITY = "image_quality"
    OCR_AI = "ocr_ai"
    DATA_VALIDITY = "data_validity"
    BUSINESS_RULE = "business_rule"
    USER_ACTION = "user_action"
    OTHER = "other"


# Mapping from reason code to category
REJECTION_CODE_TO_CATEGORY = {
    RejectionReasonCode.POOR_IMAGE_QUALITY: RejectionCategory.IMAGE_QUALITY,
    RejectionReasonCode.BLURRY_IMAGE: RejectionCategory.IMAGE_QUALITY,
    RejectionReasonCode.LOW_RESOLUTION: RejectionCategory.IMAGE_QUALITY,
    RejectionReasonCode.CUTOFF_CONTENT: RejectionCategory.IMAGE_QUALITY,
    RejectionReasonCode.WRONG_ORIENTATION: RejectionCategory.IMAGE_QUALITY,
    RejectionReasonCode.OCR_FAILED: RejectionCategory.OCR_AI,
    RejectionReasonCode.OCR_LOW_CONFIDENCE: RejectionCategory.OCR_AI,
    RejectionReasonCode.AI_EXTRACTION_FAILED: RejectionCategory.OCR_AI,
    RejectionReasonCode.AI_LOW_CONFIDENCE: RejectionCategory.OCR_AI,
    RejectionReasonCode.MISSING_CRITICAL_FIELDS: RejectionCategory.OCR_AI,
    RejectionReasonCode.DUPLICATE_RECEIPT: RejectionCategory.DATA_VALIDITY,
    RejectionReasonCode.INVALID_DATE: RejectionCategory.DATA_VALIDITY,
    RejectionReasonCode.INVALID_AMOUNT: RejectionCategory.DATA_VALIDITY,
    RejectionReasonCode.INVALID_STORE_NAME: RejectionCategory.DATA_VALIDITY,
    RejectionReasonCode.MISMATCHED_DATA: RejectionCategory.DATA_VALIDITY,
    RejectionReasonCode.NON_DEDUCTIBLE: RejectionCategory.BUSINESS_RULE,
    RejectionReasonCode.PERSONAL_EXPENSE: RejectionCategory.BUSINESS_RULE,
    RejectionReasonCode.OUT_OF_POLICY: RejectionCategory.BUSINESS_RULE,
    RejectionReasonCode.EXCEEDS_LIMIT: RejectionCategory.BUSINESS_RULE,
    RejectionReasonCode.MISSING_APPROVAL: RejectionCategory.BUSINESS_RULE,
    RejectionReasonCode.OTHER: RejectionCategory.OTHER,
    RejectionReasonCode.USER_CANCELLED: RejectionCategory.USER_ACTION,
}


@dataclass(frozen=True, slots=True)
class RejectionData:
    """Input data for creating a rejection reason.

    Attributes:
        receipt_id: Receipt being rejected.
        reason_code: Standardized reason code.
        reason_text: Human-readable reason description.
        user_note: Optional user-provided additional notes.
        is_for_ai_training: Whether this data can be used for AI training.
        ai_feedback: Optional AI-specific feedback for training.
    """

    receipt_id: int
    reason_code: str
    reason_text: str
    user_note: str | None = None
    is_for_ai_training: bool = False
    ai_feedback: str | None = None


@dataclass(frozen=True, slots=True)
class RejectionResult:
    """Result of rejection reason creation.

    Attributes:
        success: Whether the operation succeeded.
        rejection_reason_id: ID of created RejectionReason record.
        error: Error message if failed.
    """

    success: bool
    rejection_reason_id: int | None = None
    error: str | None = None


class RejectionReasonService:
    """Service for managing receipt rejection reasons.

    Single responsibility: Persist and retrieve rejection reason data
    for audit trail and future AI training.
    """

    def __init__(self, session) -> None:
        """Initialize rejection reason service.

        Args:
            session: Database session.
        """
        self._session = session

    @staticmethod
    def get_category_for_code(reason_code: str) -> RejectionCategory:
        """Get category for a reason code.

        Args:
            reason_code: Rejection reason code.

        Returns:
            Corresponding category.
        """
        return REJECTION_CODE_TO_CATEGORY.get(reason_code, RejectionCategory.OTHER)

    @staticmethod
    def validate_reason_code(reason_code: str) -> bool:
        """Validate if reason code is known.

        Args:
            reason_code: Reason code to validate.

        Returns:
            True if valid code.
        """
        return reason_code in REJECTION_CODE_TO_CATEGORY

    async def create_rejection_reason(
        self,
        data: RejectionData,
    ) -> RejectionResult:
        """Create rejection reason record for a rejected receipt.

        Implements RULE-FLOW-001-11: Store rejection reason on rejection.

        Args:
            data: Rejection data.

        Returns:
            RejectionResult with created record ID or error.
        """
        try:
            # Verify receipt exists
            receipt = await self._session.get(Receipt, data.receipt_id)
            if not receipt:
                return RejectionResult(
                    success=False,
                    error=f"Receipt not found: {data.receipt_id}",
                )

            # Check if receipt is already rejected
            if receipt.status == ReceiptStatus.REJECTED:
                return RejectionResult(
                    success=False,
                    error=f"Receipt already rejected: {data.receipt_id}",
                )

            # Check if receipt is already approved
            if receipt.status == ReceiptStatus.APPROVED:
                return RejectionResult(
                    success=False,
                    error=f"Receipt already approved: {data.receipt_id}",
                )

            # Validate reason code
            if not self.validate_reason_code(data.reason_code):
                logger.warning(
                    "Unknown rejection reason code, using OTHER category",
                    extra={"reason_code": data.reason_code},
                )

            category = self.get_category_for_code(data.reason_code)

            # Create rejection reason record
            rejection_reason = RejectionReason(
                receipt_id=data.receipt_id,
                reason_code=data.reason_code,
                reason_category=category.value,
                reason_text=data.reason_text,
                user_note=data.user_note,
                ai_feedback=data.ai_feedback,
                is_for_ai_training=data.is_for_ai_training,
            )

            self._session.add(rejection_reason)
            await self._session.flush()

            # Update receipt status to REJECTED
            receipt.status = ReceiptStatus.REJECTED
            receipt.status_message = f"却下: {data.reason_text}"

            await self._session.commit()

            logger.info(
                "Rejection reason created",
                extra={
                    "receipt_id": data.receipt_id,
                    "rejection_reason_id": rejection_reason.id,
                    "reason_code": data.reason_code,
                    "category": category.value,
                    "is_for_ai_training": data.is_for_ai_training,
                },
            )

            return RejectionResult(
                success=True,
                rejection_reason_id=rejection_reason.id,
            )

        except Exception as e:
            logger.exception(
                "Failed to create rejection reason",
                extra={"receipt_id": data.receipt_id, "error": str(e)},
            )
            await self._session.rollback()
            return RejectionResult(
                success=False,
                error=str(e),
            )

    async def get_rejection_reason(
        self,
        receipt_id: int,
    ) -> RejectionReason | None:
        """Get rejection reason for a receipt.

        Args:
            receipt_id: Receipt ID.

        Returns:
            RejectionReason if found, None otherwise.
        """
        result = await self._session.execute(
            select(RejectionReason).where(RejectionReason.receipt_id == receipt_id)
        )
        return result.scalar_one_or_none()

    async def get_rejection_reasons(
        self,
        category: RejectionCategory | None = None,
        reason_code: str | None = None,
        is_for_ai_training: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RejectionReason]:
        """Query rejection reasons with filters.

        Args:
            category: Filter by category.
            reason_code: Filter by reason code.
            is_for_ai_training: Filter by AI training flag.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            List of RejectionReason records.
        """
        stmt = select(RejectionReason)

        if category:
            stmt = stmt.where(RejectionReason.reason_category == category.value)
        if reason_code:
            stmt = stmt.where(RejectionReason.reason_code == reason_code)
        if is_for_ai_training is not None:
            stmt = stmt.where(RejectionReason.is_for_ai_training == is_for_ai_training)

        stmt = stmt.order_by(RejectionReason.created_at.desc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_ai_training_flag(
        self,
        rejection_reason_id: int,
        is_for_ai_training: bool,
        ai_feedback: str | None = None,
    ) -> bool:
        """Update AI training flag for a rejection reason.

        Args:
            rejection_reason_id: RejectionReason ID.
            is_for_ai_training: Whether to include in AI training.
            ai_feedback: Optional AI feedback text.

        Returns:
            True if updated successfully.
        """
        try:
            rejection_reason = await self._session.get(RejectionReason, rejection_reason_id)
            if not rejection_reason:
                return False

            rejection_reason.is_for_ai_training = is_for_ai_training
            if ai_feedback is not None:
                rejection_reason.ai_feedback = ai_feedback

            await self._session.commit()

            logger.info(
                "Updated AI training flag",
                extra={
                    "rejection_reason_id": rejection_reason_id,
                    "is_for_ai_training": is_for_ai_training,
                },
            )

            return True

        except Exception as e:
            logger.exception(
                "Failed to update AI training flag",
                extra={"rejection_reason_id": rejection_reason_id, "error": str(e)},
            )
            await self._session.rollback()
            return False

    async def get_stats(self) -> dict:
        """Get rejection reason statistics.

        Returns:
            Dictionary with statistics.
        """
        from sqlalchemy import func

        # Total count
        total_result = await self._session.execute(
            select(func.count(RejectionReason.id))
        )
        total = total_result.scalar() or 0

        # By category
        cat_result = await self._session.execute(
            select(
                RejectionReason.reason_category,
                func.count(RejectionReason.id),
            ).group_by(RejectionReason.reason_category)
        )
        by_category = {row[0]: row[1] for row in cat_result.fetchall()}

        # By reason code
        code_result = await self._session.execute(
            select(
                RejectionReason.reason_code,
                func.count(RejectionReason.id),
            ).group_by(RejectionReason.reason_code)
        )
        by_code = {row[0]: row[1] for row in code_result.fetchall()}

        # AI training eligible
        ai_result = await self._session.execute(
            select(func.count(RejectionReason.id)).where(
                RejectionReason.is_for_ai_training == True
            )
        )
        ai_eligible = ai_result.scalar() or 0

        return {
            "total": total,
            "by_category": by_category,
            "by_reason_code": by_code,
            "ai_training_eligible": ai_eligible,
        }

    async def export_ai_training_data(self) -> list[dict]:
        """Export rejection reasons marked for AI training.

        Returns:
            List of dictionaries with training data.
        """
        result = await self._session.execute(
            select(RejectionReason)
            .where(RejectionReason.is_for_ai_training == True)
            .order_by(RejectionReason.created_at.desc())
        )
        reasons = result.scalars().all()

        return [
            {
                "receipt_id": r.receipt_id,
                "reason_code": r.reason_code,
                "reason_category": r.reason_category,
                "reason_text": r.reason_text,
                "user_note": r.user_note,
                "ai_feedback": r.ai_feedback,
                "is_for_ai_training": r.is_for_ai_training,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reasons
        ]


async def get_rejection_reason_service(session) -> RejectionReasonService:
    """Dependency injection helper for RejectionReasonService.

    Args:
        session: Database session.

    Returns:
        RejectionReasonService instance.
    """
    return RejectionReasonService(session)