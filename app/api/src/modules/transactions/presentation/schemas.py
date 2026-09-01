from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from modules.transactions.application.use_cases.create_transaction import CreateTransactionInput


class CreateTransactionRequestSchema(BaseModel):
    """Schema Pydantic para deserializar y validar el Request HTTP."""
    user_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(INCOME|EXPENSE)$")
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="PEN", max_length=10)
    description: str = Field(default="", max_length=500)
    category_id: str = Field(default="", max_length=100)
    payment_method_id: str = Field(default="", max_length=100)
    source: str = Field(default="MANUAL", max_length=20)
    transaction_date: datetime | None = None

    def to_input_dto(self) -> CreateTransactionInput:
        """Traducción explícita del Schema HTTP al DTO de la Capa de Aplicación."""
        return CreateTransactionInput(
            user_id=self.user_id,
            account_id=self.account_id,
            type=self.type,
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            category_id=self.category_id,
            payment_method_id=self.payment_method_id,
            source=self.source,
            transaction_date=self.transaction_date,
        )


class TransactionResponseSchema(BaseModel):
    """Presenter DTO para estandarizar la salida JSON."""
    id: str
    user_id: str
    account_id: str
    type: str
    amount: Decimal
    currency: str
    description: str
    category_id: str
    payment_method_id: str
    source: str
    status: str
    transaction_date: datetime
