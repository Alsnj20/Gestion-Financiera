from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from modules.recurring_expenses.application.use_cases.create_recurring_expense import (
    CreateRecurringExpenseInput,
)


class CreateRecurringExpenseRequestSchema(BaseModel):
    account_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    frequency: str = Field(default="MONTHLY", max_length=20)
    next_date: date
    description: str = Field(default="", max_length=500)
    category_id: str = Field(default="", max_length=80)

    def to_input_dto(self, user_id: str) -> CreateRecurringExpenseInput:
        return CreateRecurringExpenseInput(
            user_id=user_id,
            account_id=self.account_id,
            amount=self.amount,
            frequency=self.frequency,
            next_date=self.next_date,
            description=self.description,
            category_id=self.category_id,
        )


class UpdateRecurringExpenseRequestSchema(BaseModel):
    """Solo metadatos: el status cambia por pause/resume/cancel."""

    amount: Decimal | None = Field(default=None, gt=0)
    frequency: str | None = Field(default=None, max_length=20)
    next_date: date | None = Field(default=None)
    description: str | None = Field(default=None, max_length=500)
    category_id: str | None = Field(default=None, max_length=80)


class RecurringExpenseResponseSchema(BaseModel):
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: Decimal
    frequency: str
    next_date: date
    description: str
    status: str
