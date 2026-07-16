"""Receipt model definition."""

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
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.duplicate_check import DuplicateCheck
    from app.models.rejection_reason import RejectionReason
    from app.models.tag import Tag


class ReceiptStatus(StrEnum):
    """Receipt processing status."""

    UNPARSED = "unparsed"  # 未解析フォルダ
    PARSING = "parsing"  # 解析中
    UNAPPROVED = "unapproved"  # 未承認フォルダ（重複チェック待ち/中）
    APPROVED = "approved"  # 承認済み（確定申告用フォルダへ移動済み）
    REJECTED = "rejected"  # 却下（失敗フォルダへ移動）
    FAILED = "failed"  # 処理失敗


class Receipt(Base, TimestampMixin):
    """Receipt model for storing receipt data."""

    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # File information
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    image_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256

    # OCR results
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_language: Mapped[str] = mapped_column(String(20), default="jpn+eng", nullable=False)

    # AI extracted fields
    receipt_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    store_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    total_amount: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )  # In yen (integer)
    tax_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="JPY", nullable=False)

    # Category and tags
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True
    )
    category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # AI analysis
    ai_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[ReceiptStatus] = mapped_column(
        Enum(ReceiptStatus, native_enum=False),
        default=ReceiptStatus.UNPARSED,
        nullable=False,
        index=True,
    )
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Processing metadata
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category", back_populates="receipts", lazy="selectin"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary="receipt_tags", back_populates="receipts", lazy="selectin"
    )
    duplicate_checks_as_source: Mapped[list["DuplicateCheck"]] = relationship(
        "DuplicateCheck",
        foreign_keys="DuplicateCheck.source_receipt_id",
        back_populates="source_receipt",
        lazy="selectin",
    )
    duplicate_checks_as_target: Mapped[list["DuplicateCheck"]] = relationship(
        "DuplicateCheck",
        foreign_keys="DuplicateCheck.target_receipt_id",
        back_populates="target_receipt",
        lazy="selectin",
    )
    rejection_reason: Mapped["RejectionReason | None"] = relationship(
        "RejectionReason", back_populates="receipt", lazy="selectin", uselist=False
    )

    # Indexes
    __table_args__ = (
        Index("ix_receipts_date_store_amount", "receipt_date", "store_name", "total_amount"),
        Index("ix_receipts_status_date", "status", "receipt_date"),
        UniqueConstraint("stored_filename", name="uq_receipts_stored_filename"),
        Index("ix_receipts_hash_status", "image_hash", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Receipt(id={self.id}, filename='{self.stored_filename}', "
            f"date={self.receipt_date}, amount={self.total_amount}, status={self.status.value})>"
        )


class ReceiptTag(Base):
    """Association table for receipts and tags."""

    __tablename__ = "receipt_tags"

    receipt_id: Mapped[int] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )



    def __repr__(self) -> str:
        return f"<ReceiptTag(receipt_id={self.receipt_id}, tag_id={self.tag_id})>"
