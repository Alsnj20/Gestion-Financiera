from __future__ import annotations

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from modules.accounts.application.use_cases.create_account import CreateAccountInput


class CreateAccountRequestSchema(BaseModel):
    """Schema Pydantic para deserializar y validar el Request HTTP."""
    name: str = Field(..., min_length=1, max_length=80)
    type: str = Field(default="OTHER", max_length=20)
    currency: str = Field(default="PEN", max_length=10)
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_default: bool = Field(default=False)

    def to_input_dto(self) -> CreateAccountInput:
        """Traducción explícita del Schema HTTP al DTO de la Capa de Aplicación."""
        return CreateAccountInput(
            user_id="",
            name=self.name,
            type=self.type,
            currency=self.currency,
            initial_balance=self.initial_balance,
            is_default=self.is_default,
        )


class UpdateAccountRequestSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    type: Optional[str] = Field(default=None, max_length=20)
    currency: Optional[str] = Field(default=None, max_length=10)
    is_default: Optional[bool] = Field(default=None)


class AccountResponseSchema(BaseModel):
    """Presenter DTO para estandarizar la salida JSON."""
    id: str
    user_id: str
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    current_balance: Decimal
    is_default: bool
    status: str
