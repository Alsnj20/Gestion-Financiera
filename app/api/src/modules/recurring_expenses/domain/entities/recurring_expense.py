from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.errors import ValidationError
from shared.types.enums import RecurrenceFrequency


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _safe_date(v: object, default: date | None = None) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip())
        except ValueError:
            return default or date.today()
    return default or date.today()


@dataclass(slots=True)
class RecurringExpense:
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: Decimal
    frequency: RecurrenceFrequency
    next_date: date
    description: str
    status: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.account_id = _safe_str(self.account_id)
        self.category_id = _safe_str(self.category_id, "")
        self.frequency = RecurrenceFrequency.safe(self.frequency)
        self.status = _safe_str(self.status, "ACTIVE").upper()
        self.description = _safe_str(self.description, "")

        self.amount = Money.from_value(self.amount).amount
        self.next_date = _safe_date(self.next_date)

        if not self.user_id:
            raise ValidationError(code="RE_USER_REQUIRED", message="user_id requerido")
        if not self.account_id:
            raise ValidationError(code="RE_ACCOUNT_REQUIRED", message="account_id requerido")
        if self.amount <= Decimal("0.00"):
            raise ValidationError(code="RE_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0")

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: Decimal | str | float | int,
        frequency: RecurrenceFrequency | str = RecurrenceFrequency.MONTHLY,
        next_date: date,
        description: str = "",
        category_id: str = "",
    ) -> RecurringExpense:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            category_id=category_id or "",
            amount=Money.from_value(amount).amount,
            frequency=RecurrenceFrequency.safe(frequency),
            next_date=next_date,
            description=description or "",
            status="ACTIVE",
            created_at=now,
        )

    @classmethod
    def rehydrate(cls, **kwargs: object) -> RecurringExpense:
        return cls(
            id=_safe_str(kwargs.get("id")) or str(uuid.uuid4()),
            user_id=_safe_str(kwargs.get("user_id"), ""),
            account_id=_safe_str(kwargs.get("account_id"), ""),
            category_id=_safe_str(kwargs.get("category_id"), ""),
            amount=Money.from_value(kwargs.get("amount")).amount if kwargs.get("amount") is not None else Decimal("0.01"),
            frequency=RecurrenceFrequency.safe(kwargs.get("frequency")),
            next_date=_safe_date(kwargs.get("next_date")),
            description=_safe_str(kwargs.get("description"), ""),
            status=_safe_str(kwargs.get("status"), "ACTIVE"),
            created_at=kwargs.get("created_at") if isinstance(kwargs.get("created_at"), datetime) else _utcnow(),
        )

    def pause(self) -> RecurringExpense:
        return RecurringExpense(
            id=self.id, user_id=self.user_id, account_id=self.account_id,
            category_id=self.category_id, amount=self.amount, frequency=self.frequency,
            next_date=self.next_date, description=self.description, status="PAUSED",
            created_at=self.created_at,
        )

    def resume(self) -> RecurringExpense:
        return RecurringExpense(
            id=self.id, user_id=self.user_id, account_id=self.account_id,
            category_id=self.category_id, amount=self.amount, frequency=self.frequency,
            next_date=self.next_date, description=self.description, status="ACTIVE",
            created_at=self.created_at,
        )

    def cancel(self) -> RecurringExpense:
        return RecurringExpense(
            id=self.id, user_id=self.user_id, account_id=self.account_id,
            category_id=self.category_id, amount=self.amount, frequency=self.frequency,
            next_date=self.next_date, description=self.description, status="CANCELLED",
            created_at=self.created_at,
        )
