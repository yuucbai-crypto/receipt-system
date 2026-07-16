"""Rejection reason model definition."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.receipt import Receipt


class RejectionReason(Base, TimestampMixin):
    """Rejection reason model for storing rejection reasons of rejected receipts."""

    __tablename__ = "rejection_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Associated receipt (one-to-one)
    receipt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("receipts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Reason classification
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reason_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Detailed reason
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI learning metadata
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)  # For future AI training
    is_for_ai_training: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    # Relationship
    receipt: Mapped["Receipt"] = relationship(
        "Receipt", back_populates="rejection_reason", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<RejectionReason(id={self.id}, receipt={self.receipt_id}, code='{self.reason_code}')>"
        )
