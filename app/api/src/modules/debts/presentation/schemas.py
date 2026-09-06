from __future__ import annotations

from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Optional
from modules.debts.application.use_cases.create_debt import CreateDebtInput


class CreateDebtRequestSchema(BaseModel):
    creditor_name: str = Field(..., min_length=1, max_length=120)
    principal_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    interest_rate_type: str = Field(default="PERCENTAGE", max_length=20)
    payment_frequency: str = Field(default="MONTHLY", max_length=20)
    installment_count: int = Field(default=1, ge=1)
    installment_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    start_date: date | None = None
    first_due_date: date | None = None
    amortization_method: str = Field(default="SIMPLE", max_length=20)
    notes: str = Field(default="", max_length=1000)

    def to_input_dto(self) -> CreateDebtInput:
        return CreateDebtInput(user_id="", creditor_name=self.creditor_name, principal_amount=self.principal_amount, interest_rate=self.interest_rate, interest_rate_type=self.interest_rate_type, payment_frequency=self.payment_frequency, installment_count=self.installment_count, installment_amount=self.installment_amount, start_date=self.start_date, first_due_date=self.first_due_date, amortization_method=self.amortization_method, notes=self.notes)


class UpdateDebtRequestSchema(BaseModel):
    creditor_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    interest_rate: Optional[Decimal] = Field(default=None, ge=0)
    payment_frequency: Optional[str] = Field(default=None, max_length=20)
    installment_count: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, max_length=20)


class DebtResponseSchema(BaseModel):
    id: str
    user_id: str
    creditor_name: str
    principal_amount: Decimal
    status: str
