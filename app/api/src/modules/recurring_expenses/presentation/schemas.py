from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from modules.recurring_expenses.application.use_cases.create_recurring_expense import CreateRecurringExpenseInput


class CreateRecurringExpenseRequestSchema(BaseModel):
    account_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    frequency: str = Field(default="MONTHLY", max_length=20)
    next_date: date
    description: str = Field(default="", max_length=500)
    category_id: str = Field(default="", max_length=80)

    def to_input_dto(self) -> CreateRecurringExpenseInput:
        return CreateRecurringExpenseInput(
            user_id="",
            account_id=self.account_id,
            amount=self.amount,
            frequency=self.frequency,
            next_date=self.next_date,
            description=self.description,
            category_id=self.category_id,
        )


class UpdateRecurringExpenseRequestSchema(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    frequency: Optional[str] = Field(default=None, max_length=20)
    next_date: Optional[date] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default=None, max_length=20)


class RecurringExpenseResponseSchema(BaseModel):
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: str
    frequency: str
    next_date: str
    description: str
    status: str
