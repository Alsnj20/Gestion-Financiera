from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from modules.accounts.application.use_cases.create_account import (
    CreateAccountInput,
)


class CreateAccountRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: str = Field(default="OTHER", max_length=20)
    currency: str = Field(default="PEN", max_length=10)
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_default: bool = Field(default=False)

    def to_input_dto(self, user_id: str) -> CreateAccountInput:
        return CreateAccountInput(
            user_id=user_id,
            name=self.name,
            type=self.type,
            currency=self.currency,
            initial_balance=self.initial_balance,
            is_default=self.is_default,
        )


class UpdateAccountRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    type: str | None = Field(default=None, max_length=20)
    is_default: bool | None = None


class AccountResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    current_balance: Decimal
    is_default: bool
    status: str
