from pydantic import BaseModel, Field
from decimal import Decimal
from modules.limits.application.use_cases.create_limit import CreateLimitInput


class CreateLimitRequestSchema(BaseModel):
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=120)
    amount: Decimal = Field(..., gt=0)
    period_type: str = Field(default="MONTHLY", max_length=20)
    category_id: str = Field(default="", max_length=100)
    threshold_warning: Decimal = Field(default=Decimal("80"), ge=0, le=100)

    def to_input_dto(self) -> CreateLimitInput:
        return CreateLimitInput(user_id=self.user_id, name=self.name, amount=self.amount, period_type=self.period_type, category_id=self.category_id, threshold_warning=self.threshold_warning)


class LimitResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_type: str
    category_id: str
    threshold_warning: Decimal
    status: str
