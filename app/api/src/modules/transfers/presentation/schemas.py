from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from modules.transfers.application.use_cases.create_transfer import CreateTransferInput


class CreateTransferRequestSchema(BaseModel):
    source_account_id: str = Field(..., min_length=1)
    destination_account_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="PEN", max_length=10)
    description: str = Field(default="", max_length=500)
    date: datetime | None = None

    def to_input_dto(self) -> CreateTransferInput:
        return CreateTransferInput(user_id="", source_account_id=self.source_account_id, destination_account_id=self.destination_account_id, amount=self.amount, currency=self.currency, description=self.description, date=self.date)


class TransferResponseSchema(BaseModel):
    id: str
    user_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str
