"""Report schemas for financial summaries."""
from pydantic import BaseModel
from decimal import Decimal


class SummaryResponseSchema(BaseModel):
    user_id: str
    period_start: str
    period_end: str
    total_income: str
    total_expenses: str
    net_balance: str
    transaction_count: int


class CategoryBreakdownSchema(BaseModel):
    category_id: str
    category_name: str
    total_amount: str
    transaction_count: int
    percentage: str


class ByCategoryResponseSchema(BaseModel):
    user_id: str
    period_start: str
    period_end: str
    type: str  # INCOME o EXPENSE
    categories: list[CategoryBreakdownSchema]
    total: str


class AccountBreakdownSchema(BaseModel):
    account_id: str
    account_name: str
    total_income: str
    total_expenses: str
    net_balance: str
    transaction_count: int


class ByAccountResponseSchema(BaseModel):
    user_id: str
    period_start: str
    period_end: str
    accounts: list[AccountBreakdownSchema]
