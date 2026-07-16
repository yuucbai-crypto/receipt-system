"""Tag model definition."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.receipt import Receipt


class Tag(Base, TimestampMixin):
    """Tag model for flexible tagging of receipts."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Tag identification
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Display
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color #RRGGBB
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # System
    is_system: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt", secondary="receipt_tags", back_populates="tags", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}', slug='{self.slug}')>"
