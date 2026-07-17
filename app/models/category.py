"""Category model definition."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.receipt import Receipt


class Category(Base, TimestampMixin):
    """Category model for accounting categories (勘定科目)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Category identification
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Hierarchy support (simplified - single level)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color code #RRGGBB
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tax related
    is_tax_deductible: Mapped[bool] = mapped_column(default=True, nullable=False)
    tax_category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # System
    is_system: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Relationships
    parent: Mapped["Category | None"] = relationship(
        "Category", back_populates="children", remote_side="Category.id", lazy="selectin"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", lazy="selectin"
    )
    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt", back_populates="category", lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("parent_id", "code", name="uq_category_parent_code"),
        Index("ix_categories_parent_active", "parent_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, code='{self.code}', name='{self.name}')>"

    @property
    def full_code(self) -> str:
        """Get full hierarchical code."""
        if self.parent:
            return f"{self.parent.full_code}.{self.code}"
        return self.code

    @property
    def full_name(self) -> str:
        """Get full hierarchical name."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name
