from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from modules.debts.application.use_cases.create_debt import CreateDebtInput


class CreateDebtRequestSchema(BaseModel):
    creditor_name: str = Field(min_length=1, max_length=120)
    principal_amount: Decimal = Field(gt=0)
    interest_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    interest_rate_type: str = Field(default="PERCENTAGE", max_length=20)
    payment_frequency: str = Field(default="MONTHLY", max_length=20)
    installment_count: int = Field(default=1, ge=1)
    installment_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    start_date: date | None = None
    first_due_date: date | None = None
    amortization_method: str = Field(default="SIMPLE", max_length=20)
    notes: str = Field(default="", max_length=1000)

    def to_input_dto(self, user_id: str) -> CreateDebtInput:
        return CreateDebtInput(
            user_id=user_id,
            creditor_name=self.creditor_name,
            principal_amount=self.principal_amount,
            interest_rate=self.interest_rate,
            interest_rate_type=self.interest_rate_type,
            payment_frequency=self.payment_frequency,
            installment_count=self.installment_count,
            installment_amount=self.installment_amount,
            start_date=self.start_date,
            first_due_date=self.first_due_date,
            amortization_method=self.amortization_method,
            notes=self.notes,
        )


class UpdateDebtRequestSchema(BaseModel):
    """Solo metadatos: el principal/condiciones/status no se editan por PUT."""

    creditor_name: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)


class InstallmentResponseSchema(BaseModel):
    id: str
    number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    status: str


class PaymentResponseSchema(BaseModel):
    id: str
    installment_id: str
    transaction_id: str
    payment_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal


class RegisterPaymentResponseSchema(BaseModel):
    payment_id: str
    debt_id: str
    installment_id: str
    transaction_id: str
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    installment_status: str
    debt_status: str


class RegisterPaymentRequestSchema(BaseModel):
    account_id: str = Field(min_length=1)
    installment_id: str = Field(min_length=1)
    principal_amount: Decimal = Field(ge=0)
    interest_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_date: date | None = None
    category_id: str = Field(default="", max_length=100)
    payment_method_id: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=500)


class DebtResponseSchema(BaseModel):
    id: str
    user_id: str
    creditor_name: str
    principal_amount: Decimal
    status: str
    installments: list[InstallmentResponseSchema] = Field(default_factory=list)
    payments: list[PaymentResponseSchema] = Field(default_factory=list)
