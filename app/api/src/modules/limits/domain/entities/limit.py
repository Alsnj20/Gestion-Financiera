from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.errors import ValidationError
from shared.types.enums import BudgetStatus, PeriodType

MAX_NAME_LEN = 120


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class Limit:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_type: PeriodType = PeriodType.MONTHLY
    category_id: str = ""
    threshold_warning: Decimal = Decimal("80")
    status: BudgetStatus = BudgetStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.name = _safe_str(self.name)
        self.category_id = _safe_str(self.category_id, "")
        self.period_type = PeriodType.safe(self.period_type)
        self.status = BudgetStatus.safe(self.status)
        self.amount = Money.from_value(self.amount).amount
        # Normaliza porcentaje 0..100
        try:
            tw = Decimal(str(self.threshold_warning)) if self.threshold_warning is not None else Decimal("80")
        except Exception:
            tw = Decimal("80")
        if tw < Decimal("0"):
            tw = Decimal("0")
        if tw > Decimal("100"):
            tw = Decimal("100")
        self.threshold_warning = tw

        if self.amount <= Decimal("0.00"):
            raise ValidationError(code="LIMIT_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0")

    @classmethod
    def create(cls, *, user_id: str, name: str, amount: Decimal | str | float | int, period_type: PeriodType | str = PeriodType.MONTHLY, category_id: str = "", threshold_warning: Decimal | str | float | int = Decimal("80")) -> Limit:
        return cls(id=str(uuid.uuid4()), user_id=user_id, name=name, amount=Money.from_value(amount).amount, period_type=PeriodType.safe(period_type), category_id=category_id or "", threshold_warning=Money.from_value(threshold_warning).amount, created_at=_utcnow())
