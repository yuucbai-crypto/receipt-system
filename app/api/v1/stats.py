"""API endpoints for statistics (separate endpoints for dashboard).

Implements RULE-BE-007, RULE-BE-008: Summary calculations for tax filing.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db_session_dep
from app.api.v1.schemas.stats import (
    CategoryStatItem,
    MonthlyStatItem,
    StatSummaryResponse,
)
from app.core.logging import get_logger
from app.models.receipt import Receipt, ReceiptStatus

logger = get_logger(__name__)

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/summary",
    response_model=StatSummaryResponse,
    status_code=200,
    summary="ダッシュボード用サマリ取得",
    description="ダッシュボード表示用の集計データを取得します（今月・今年・カテゴリ別・月別推移）。",
)
async def get_stats_summary(
    session: Annotated[AsyncSession, Depends(get_db_session_dep)],
) -> StatSummaryResponse:
    """Get dashboard summary statistics.

    Returns:
        StatSummaryResponse with monthly/yearly/category totals.
    """
    now = datetime.now(timezone.utc)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate current month total
    current_month_stmt = (
        select(func.coalesce(func.sum(Receipt.total_amount), 0))
        .where(Receipt.status == ReceiptStatus.APPROVED)
        .where(Receipt.receipt_date >= current_month_start)
    )
    current_month_result = await session.execute(current_month_stmt)
    current_month_total = int(current_month_result.scalar() or 0)

    # Calculate yearly total
    yearly_stmt = (
        select(func.coalesce(func.sum(Receipt.total_amount), 0))
        .where(Receipt.status == ReceiptStatus.APPROVED)
        .where(Receipt.receipt_date >= current_year_start)
    )
    yearly_result = await session.execute(yearly_stmt)
    yearly_total = int(yearly_result.scalar() or 0)

    # Calculate category totals
    category_stmt = (
        select(
            Receipt.category_id,
            func.coalesce(func.sum(Receipt.total_amount), 0).label("total"),
        )
        .where(Receipt.status == ReceiptStatus.APPROVED)
        .group_by(Receipt.category_id)
    )
    category_result = await session.execute(category_stmt)
    category_totals: dict[str, int] = {}
    for row in category_result.fetchall():
        category_name = f"Category {row.category_id}" if row.category_id else "Uncategorized"
        category_totals[category_name] = int(row.total or 0)

    # Calculate monthly trend (last 12 months)
    monthly_stmt = (
        select(
            func.strftime("%Y-%m", Receipt.receipt_date).label("month"),
            func.coalesce(func.sum(Receipt.total_amount), 0).label("total"),
        )
        .where(Receipt.status == ReceiptStatus.APPROVED)
        .where(Receipt.receipt_date >= current_year_start)
        .group_by(func.strftime("%Y-%m", Receipt.receipt_date))
        .order_by(func.strftime("%Y-%m", Receipt.receipt_date))
    )
    monthly_result = await session.execute(monthly_stmt)
    monthly_trend = [
        MonthlyStatItem(month=row.month, total_amount=int(row.total or 0), receipt_count=0)
        for row in monthly_result.fetchall()
    ]

    logger.info(
        "Stats summary retrieved",
        extra={
            "current_month_total": current_month_total,
            "yearly_total": yearly_total,
        },
    )

    return StatSummaryResponse(
        current_month_total=current_month_total,
        yearly_total=yearly_total,
        category_totals=category_totals,
        monthly_trend=monthly_trend,
    )


@router.get(
    "/monthly",
    response_model=list[MonthlyStatItem],
    status_code=200,
    summary="月別推移取得",
    description="月別のレシート集計データを取得します。",
)
async def get_monthly_stats(
    session: Annotated[AsyncSession, Depends(get_db_session_dep)],
) -> list[MonthlyStatItem]:
    """Get monthly statistics.

    Returns:
        List of MonthlyStatItem.
    """
    now = datetime.now(timezone.utc)
    current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_stmt = (
        select(
            func.strftime("%Y-%m", Receipt.receipt_date).label("month"),
            func.coalesce(func.sum(Receipt.total_amount), 0).label("total_amount"),
            func.count(Receipt.id).label("receipt_count"),
        )
        .where(Receipt.status == ReceiptStatus.APPROVED)
        .where(Receipt.receipt_date >= current_year_start)
        .group_by(func.strftime("%Y-%m", Receipt.receipt_date))
        .order_by(func.strftime("%Y-%m", Receipt.receipt_date))
    )
    monthly_result = await session.execute(monthly_stmt)

    return [
        MonthlyStatItem(
            month=row.month,
            total_amount=int(row.total_amount or 0),
            receipt_count=int(row.receipt_count or 0),
        )
        for row in monthly_result.fetchall()
    ]


@router.get(
    "/by-category",
    response_model=list[CategoryStatItem],
    status_code=200,
    summary="勘定科目別集計取得",
    description="勘定科目別のレシート集計データを取得します。",
)
async def get_category_stats(
    session: Annotated[AsyncSession, Depends(get_db_session_dep)],
) -> list[CategoryStatItem]:
    """Get category statistics.

    Returns:
        List of CategoryStatItem.
    """
    category_stmt = (
        select(
            Receipt.category_id,
            func.coalesce(func.sum(Receipt.total_amount), 0).label("total_amount"),
            func.count(Receipt.id).label("receipt_count"),
        )
        .where(Receipt.status == ReceiptStatus.APPROVED)
        .group_by(Receipt.category_id)
    )
    category_result = await session.execute(category_stmt)

    return [
        CategoryStatItem(
            category_name=f"Category {row.category_id}" if row.category_id else "Uncategorized",
            total_amount=int(row.total_amount or 0),
            receipt_count=int(row.receipt_count or 0),
        )
        for row in category_result.fetchall()
    ]