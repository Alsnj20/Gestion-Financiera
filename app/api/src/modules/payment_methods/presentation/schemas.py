from pydantic import BaseModel, Field
from modules.payment_methods.application.use_cases.create_payment_method import CreatePaymentMethodInput


class CreatePaymentMethodRequestSchema(BaseModel):
    user_id: str = Field(..., min_length=1)
    account_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=60)
    type: str = Field(default="", max_length=60)
    is_default: bool = Field(default=False)

    def to_input_dto(self) -> CreatePaymentMethodInput:
        return CreatePaymentMethodInput(user_id=self.user_id, account_id=self.account_id, name=self.name, type=self.type, is_default=self.is_default)


class PaymentMethodResponseSchema(BaseModel):
    id: str
    user_id: str
    account_id: str
    name: str
    type: str
    is_default: bool
    status: str
