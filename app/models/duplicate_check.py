"""Duplicate check model definition."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.receipt import Receipt


class DuplicateCheckStatus(StrEnum):
    """Duplicate check status."""

    PENDING = "pending"  # チェック待ち
    PROCESSING = "processing"  # チェック中
    COMPLETED = "completed"  # チェック完了
    NO_DUPLICATES = "no_duplicates"  # 重複なし
    HAS_DUPLICATES = "has_duplicates"  # 重複あり
    USER_REVIEWED = "user_reviewed"  # ユーザー確認済み
    FAILED = "failed"  # チェック失敗


class DuplicateCheck(Base, TimestampMixin):
    """Duplicate check model for tracking duplicate detection results."""

    __tablename__ = "duplicate_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Receipt references
    source_receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Comparison scores (0.0 - 1.0)
    store_name_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    date_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_hash_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Thresholds used
    duplicate_threshold: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)

    # Result
    is_duplicate: Mapped[bool | None] = mapped_column(nullable=True, index=True)
    status: Mapped[DuplicateCheckStatus] = mapped_column(
        Enum(DuplicateCheckStatus, native_enum=False),
        default=DuplicateCheckStatus.PENDING,
        nullable=False,
        index=True,
    )

    # User review
    user_confirmed: Mapped[bool | None] = mapped_column(nullable=True)
    user_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Processing metadata
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source_receipt: Mapped["Receipt"] = relationship(
        "Receipt",
        foreign_keys=[source_receipt_id],
        back_populates="duplicate_checks_as_source",
        lazy="selectin",
    )
    target_receipt: Mapped["Receipt"] = relationship(
        "Receipt",
        foreign_keys=[target_receipt_id],
        back_populates="duplicate_checks_as_target",
        lazy="selectin",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("source_receipt_id", "target_receipt_id", name="uq_duplicate_check_pair"),
        Index("ix_duplicate_checks_source_status", "source_receipt_id", "status"),
        Index("ix_duplicate_checks_composite_score", "composite_score"),
        Index("ix_duplicate_checks_user_review", "user_confirmed", "user_reviewed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<DuplicateCheck(id={self.id}, source={self.source_receipt_id}, "
            f"target={self.target_receipt_id}, score={self.composite_score}, "
            f"duplicate={self.is_duplicate}, status={self.status.value})>"
        )

    def mark_failed(self, error: Exception) -> None:
        """Mark the duplicate check as failed with error details.

        Args:
            error: Exception that caused the failure
        """
        self.status = DuplicateCheckStatus.FAILED
        self.error_message = str(error)
        self.processing_completed_at = datetime.utcnow()

    def mark_completed(self, is_duplicate: bool, composite_score: float) -> None:
        """Mark the duplicate check as completed.

        Args:
            is_duplicate: Whether duplicate was detected
            composite_score: Composite similarity score
        """
        self.status = (
            DuplicateCheckStatus.HAS_DUPLICATES if is_duplicate else DuplicateCheckStatus.NO_DUPLICATES
        )
        self.is_duplicate = is_duplicate
        self.composite_score = composite_score
        self.processing_completed_at = datetime.utcnow()
