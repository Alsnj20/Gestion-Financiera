from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from modules.limits.application.use_cases.create_limit import CreateLimitInput


class CreateLimitRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    period_type: str = Field(default="MONTHLY", max_length=20)
    category_id: str = Field(default="", max_length=100)
    threshold_warning: Decimal = Field(default=Decimal(80), ge=0, le=100)

    def to_input_dto(self, user_id: str) -> CreateLimitInput:
        return CreateLimitInput(
            user_id=user_id,
            name=self.name,
            amount=self.amount,
            period_type=self.period_type,
            category_id=self.category_id,
            threshold_warning=self.threshold_warning,
        )


class UpdateLimitRequestSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    amount: Decimal | None = Field(default=None, gt=0)
    period_type: str | None = Field(default=None, max_length=20)
    category_id: str | None = Field(default=None, max_length=100)
    threshold_warning: Decimal | None = Field(default=None, ge=0, le=100)


class LimitResponseSchema(BaseModel):
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_type: str
    category_id: str
    threshold_warning: Decimal
    status: str
