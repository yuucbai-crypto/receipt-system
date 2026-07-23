"""Pydantic schemas for statistics API."""

from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel


class StatSummaryItem(BaseModel):
    """Stat summary item schema."""

    current_month_total: int
    yearly_total: int
    category_totals: Dict[str, int]
    monthly_trend: List[Dict[str, object]]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MonthlyStatItem(BaseModel):
    """Monthly statistics item schema."""

    month: str
    total_amount: int
    receipt_count: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CategoryStatItem(BaseModel):
    """Category statistics item schema."""

    category_name: str
    total_amount: int
    receipt_count: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class StatSummaryResponse(BaseModel):
    """Stat summary response schema."""

    current_month_total: int
    yearly_total: int
    category_totals: Dict[str, int]
    monthly_trend: List[MonthlyStatItem]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MonthlyStatsResponse(BaseModel):
    """Monthly stats response schema."""

    items: List[MonthlyStatItem]
    total: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CategoryStatsResponse(BaseModel):
    """Category stats response schema."""

    items: List[CategoryStatItem]
    total: int

    class Config:
        """Pydantic configuration."""

        from_attributes = True