"""Reports router with summary, by-category, and by-account endpoints."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.session import get_session
from infrastructure.database.models import TransactionModel, CategoryModel, AccountModel
from modules.reports.presentation.schemas import (
    SummaryResponseSchema,
    ByCategoryResponseSchema,
    CategoryBreakdownSchema,
    ByAccountResponseSchema,
    AccountBreakdownSchema,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_month_range(reference_date: date | None = None) -> tuple[date, date]:
    """Get start and end dates for a month."""
    ref = reference_date or date.today()
    start = ref.replace(day=1)
    if ref.month == 12:
        end = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = ref.replace(month=ref.month + 1, day=1) - timedelta(days=1)
    return start, end


@router.get("/summary", response_model=SummaryResponseSchema)
async def get_summary(
    user_id: str,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2020, le=2100),
    session: AsyncSession = Depends(get_session),
):
    """Get income vs expenses summary for a period."""
    today = date.today()
    ref_date = date(year or today.year, month or today.month, 1)
    period_start, period_end = _get_month_range(ref_date)

    # Get income total
    income_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
        TransactionModel.user_id == user_id,
        TransactionModel.type == "INCOME",
        TransactionModel.status == "COMPLETED",
        TransactionModel.transaction_date >= period_start,
        TransactionModel.transaction_date <= period_end + timedelta(days=1),
    )
    income_result = await session.execute(income_stmt)
    total_income = income_result.scalar() or Decimal("0.00")

    # Get expense total
    expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
        TransactionModel.user_id == user_id,
        TransactionModel.type == "EXPENSE",
        TransactionModel.status == "COMPLETED",
        TransactionModel.transaction_date >= period_start,
        TransactionModel.transaction_date <= period_end + timedelta(days=1),
    )
    expense_result = await session.execute(expense_stmt)
    total_expenses = expense_result.scalar() or Decimal("0.00")

    # Get transaction count
    count_stmt = select(func.count(TransactionModel.id)).where(
        TransactionModel.user_id == user_id,
        TransactionModel.status == "COMPLETED",
        TransactionModel.transaction_date >= period_start,
        TransactionModel.transaction_date <= period_end + timedelta(days=1),
    )
    count_result = await session.execute(count_stmt)
    tx_count = count_result.scalar() or 0

    return SummaryResponseSchema(
        user_id=user_id,
        period_start=str(period_start),
        period_end=str(period_end),
        total_income=str(total_income),
        total_expenses=str(total_expenses),
        net_balance=str(total_income - total_expenses),
        transaction_count=tx_count,
    )


@router.get("/by-category", response_model=ByCategoryResponseSchema)
async def get_by_category(
    user_id: str,
    type: str = Query("EXPENSE", regex="^(INCOME|EXPENSE)$"),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2020, le=2100),
    session: AsyncSession = Depends(get_session),
):
    """Get transactions grouped by category."""
    today = date.today()
    ref_date = date(year or today.year, month or today.month, 1)
    period_start, period_end = _get_month_range(ref_date)

    # Get transactions grouped by category
    stmt = (
        select(
            TransactionModel.category_id,
            func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
            func.count(TransactionModel.id).label("count"),
        )
        .where(
            TransactionModel.user_id == user_id,
            TransactionModel.type == type,
            TransactionModel.status == "COMPLETED",
            TransactionModel.transaction_date >= period_start,
            TransactionModel.transaction_date <= period_end + timedelta(days=1),
        )
        .group_by(TransactionModel.category_id)
    )
    result = await session.execute(stmt)
    rows = result.all()

    # Calculate grand total
    grand_total = sum(row.total for row in rows) or Decimal("0.00")

    categories = []
    for row in rows:
        # Get category name
        cat_name = "Sin categoría"
        if row.category_id:
            cat_stmt = select(CategoryModel.name).where(CategoryModel.id == row.category_id)
            cat_result = await session.execute(cat_stmt)
            cat_name = cat_result.scalar() or "Sin categoría"

        percentage = (row.total / grand_total * 100) if grand_total > 0 else Decimal("0.00")
        categories.append(
            CategoryBreakdownSchema(
                category_id=row.category_id or "",
                category_name=cat_name,
                total_amount=str(row.total),
                transaction_count=row.count,
                percentage=str(round(percentage, 2)),
            )
        )

    # Sort by total descending
    categories.sort(key=lambda c: Decimal(c.total_amount), reverse=True)

    return ByCategoryResponseSchema(
        user_id=user_id,
        period_start=str(period_start),
        period_end=str(period_end),
        type=type,
        categories=categories,
        total=str(grand_total),
    )


@router.get("/by-account", response_model=ByAccountResponseSchema)
async def get_by_account(
    user_id: str,
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=2020, le=2100),
    session: AsyncSession = Depends(get_session),
):
    """Get transactions grouped by account."""
    today = date.today()
    ref_date = date(year or today.year, month or today.month, 1)
    period_start, period_end = _get_month_range(ref_date)

    # Get all accounts for user
    accounts_stmt = select(AccountModel).where(AccountModel.user_id == user_id)
    accounts_result = await session.execute(accounts_stmt)
    accounts = accounts_result.scalars().all()

    account_breakdowns = []
    for account in accounts:
        # Get income for this account
        income_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.account_id == account.id,
            TransactionModel.type == "INCOME",
            TransactionModel.status == "COMPLETED",
            TransactionModel.transaction_date >= period_start,
            TransactionModel.transaction_date <= period_end + timedelta(days=1),
        )
        income_result = await session.execute(income_stmt)
        account_income = income_result.scalar() or Decimal("0.00")

        # Get expenses for this account
        expense_stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.account_id == account.id,
            TransactionModel.type == "EXPENSE",
            TransactionModel.status == "COMPLETED",
            TransactionModel.transaction_date >= period_start,
            TransactionModel.transaction_date <= period_end + timedelta(days=1),
        )
        expense_result = await session.execute(expense_stmt)
        account_expenses = expense_result.scalar() or Decimal("0.00")

        # Get transaction count
        count_stmt = select(func.count(TransactionModel.id)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.account_id == account.id,
            TransactionModel.status == "COMPLETED",
            TransactionModel.transaction_date >= period_start,
            TransactionModel.transaction_date <= period_end + timedelta(days=1),
        )
        count_result = await session.execute(count_stmt)
        tx_count = count_result.scalar() or 0

        account_breakdowns.append(
            AccountBreakdownSchema(
                account_id=str(account.id),
                account_name=account.name,
                total_income=str(account_income),
                total_expenses=str(account_expenses),
                net_balance=str(account_income - account_expenses),
                transaction_count=tx_count,
            )
        )

    return ByAccountResponseSchema(
        user_id=user_id,
        period_start=str(period_start),
        period_end=str(period_end),
        accounts=account_breakdowns,
    )
