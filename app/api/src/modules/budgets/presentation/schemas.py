from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from modules.budgets.application.use_cases.create_budget import CreateBudgetInput


class CreateBudgetRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    period_start: date
    period_end: date
    category_id: str = Field(default="", max_length=100)

    def to_input_dto(self, user_id: str) -> CreateBudgetInput:
        return CreateBudgetInput(
            user_id=user_id,
            name=self.name,
            amount=self.amount,
            period_start=self.period_start,
            period_end=self.period_end,
            category_id=self.category_id,
        )


class UpdateBudgetRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0)
    period_start: date | None = Field(default=None)
    period_end: date | None = Field(default=None)
    category_id: str | None = Field(default=None, max_length=100)


class BudgetResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str
    status: str
