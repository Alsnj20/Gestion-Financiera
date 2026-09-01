from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.types.enums import BudgetStatus

MAX_NAME_LEN = 120


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _safe_date(v: object) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip())
        except ValueError:
            return date.today()
    return date.today()


@dataclass(slots=True)
class Budget:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str = ""  # "" = presupuesto general
    status: BudgetStatus = BudgetStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.name = _safe_str(self.name)
        self.category_id = _safe_str(self.category_id, "")
        self.status = BudgetStatus.safe(self.status)
        self.amount = Money.from_value(self.amount).amount
        self.period_start = _safe_date(self.period_start)
        self.period_end = _safe_date(self.period_end)

    @classmethod
    def create(cls, *, user_id: str, name: str, amount: Decimal | str | float | int, period_start: date, period_end: date, category_id: str = "") -> Budget:
        return cls(id=str(uuid.uuid4()), user_id=user_id, name=name, amount=Money.from_value(amount).amount, period_start=period_start, period_end=period_end, category_id=category_id or "", created_at=_utcnow())

    @classmethod
    def rehydrate(cls, **kwargs: object) -> Budget:  # type: ignore[no-untyped-def]
        return cls(
            id=_safe_str(kwargs.get("id")) or str(uuid.uuid4()),
            user_id=_safe_str(kwargs.get("user_id"), ""),
            name=_safe_str(kwargs.get("name"), "Budget"),
            amount=Money.from_value(kwargs.get("amount")).amount if kwargs.get("amount") is not None else Decimal("0.00"),
            period_start=_safe_date(kwargs.get("period_start")),
            period_end=_safe_date(kwargs.get("period_end")),
            category_id=_safe_str(kwargs.get("category_id"), ""),
            status=BudgetStatus.safe(kwargs.get("status")),
            created_at=kwargs.get("created_at") if isinstance(kwargs.get("created_at"), datetime) else _utcnow(),
        )
