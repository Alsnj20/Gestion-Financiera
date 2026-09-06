from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from modules.budgets.application.use_cases.create_budget import CreateBudgetInput


class CreateBudgetRequestSchema(BaseModel):
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=120)
    amount: Decimal = Field(..., gt=0)
    period_start: date
    period_end: date
    category_id: str = Field(default="", max_length=100)

    def to_input_dto(self) -> CreateBudgetInput:
        return CreateBudgetInput(user_id=self.user_id, name=self.name, amount=self.amount, period_start=self.period_start, period_end=self.period_end, category_id=self.category_id)


class BudgetResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str
    status: str
