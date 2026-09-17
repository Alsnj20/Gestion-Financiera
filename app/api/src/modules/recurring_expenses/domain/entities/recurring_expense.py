from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from shared.domain.guards import clean_str, safe_date, today
from shared.domain.guards import utcnow as _utcnow
from shared.domain.value_objects.money import Money
from shared.errors import ValidationError
from shared.types.enums import RecurrenceFrequency, RecurringStatus


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="RE_ID_REQUIRED", message="id requerido")
    return cleaned


@dataclass(slots=True, frozen=True)
class RecurringExpense:
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: Decimal
    frequency: RecurrenceFrequency
    next_date: date
    description: str
    status: RecurringStatus
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="RE_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        account_id = clean_str(self.account_id)
        if not account_id:
            raise ValidationError(
                code="RE_ACCOUNT_REQUIRED", message="account_id requerido"
            )
        object.__setattr__(self, "account_id", account_id)
        object.__setattr__(self, "category_id", clean_str(self.category_id))
        object.__setattr__(self, "frequency", RecurrenceFrequency.safe(self.frequency))
        object.__setattr__(self, "status", RecurringStatus.safe(self.status))
        object.__setattr__(self, "description", clean_str(self.description))
        amount = Money.from_value(self.amount).amount
        if amount <= Decimal("0.00"):
            raise ValidationError(
                code="RE_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
            )
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "next_date", safe_date(self.next_date))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: Decimal | str | float,
        frequency: RecurrenceFrequency | str = RecurrenceFrequency.MONTHLY,
        next_date: date | None = None,
        description: str = "",
        category_id: str = "",
    ) -> RecurringExpense:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            category_id=category_id or "",
            amount=amount,
            frequency=RecurrenceFrequency.safe(frequency),
            next_date=next_date or today(),
            description=description or "",
            status=RecurringStatus.ACTIVE,
            created_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        account_id: object,
        category_id: object = "",
        amount: object = None,
        frequency: object = RecurrenceFrequency.MONTHLY,
        next_date: object = None,
        description: object = "",
        status: object = RecurringStatus.ACTIVE,
        created_at: object = None,
    ) -> RecurringExpense:
        # Sin monto mágico: None/0 falla en __post_init__ con RE_AMOUNT_NOT_POSITIVE.
        value = (
            Money.from_value(amount).amount if amount is not None else Decimal("0.00")
        )
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            account_id=clean_str(account_id, ""),
            category_id=clean_str(category_id, ""),
            amount=value,
            frequency=RecurrenceFrequency.safe(frequency),
            next_date=safe_date(next_date),
            description=clean_str(description, ""),
            status=RecurringStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
        )

    def is_active(self) -> bool:
        return self.status == RecurringStatus.ACTIVE

    def is_cancelled(self) -> bool:
        return self.status == RecurringStatus.CANCELLED

    def update_details(
        self,
        *,
        amount: Decimal | None = None,
        frequency: RecurrenceFrequency | str | None = None,
        next_date: date | None = None,
        description: str | None = None,
        category_id: str | None = None,
    ) -> RecurringExpense:
        self._ensure_mutable("editarse")
        if amount is not None:
            value = Money.from_value(amount).amount
            if value <= Decimal("0.00"):
                raise ValidationError(
                    code="RE_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
                )
        else:
            value = self.amount
        return self._with(
            amount=value,
            frequency=RecurrenceFrequency.safe(frequency)
            if frequency is not None
            else self.frequency,
            next_date=safe_date(next_date) if next_date is not None else self.next_date,
            description=clean_str(description)
            if description is not None
            else self.description,
            category_id=clean_str(category_id)
            if category_id is not None
            else self.category_id,
        )

    def pause(self) -> RecurringExpense:
        self._ensure_mutable("pausarse")
        if not self.is_active():
            return self
        return self._with(status=RecurringStatus.PAUSED)

    def resume(self) -> RecurringExpense:
        self._ensure_mutable("reanudarse")
        return self._with(status=RecurringStatus.ACTIVE)

    def cancel(self) -> RecurringExpense:
        self._ensure_mutable("cancelarse")
        if self.is_cancelled():
            return self
        return self._with(status=RecurringStatus.CANCELLED)

    def _ensure_mutable(self, action_description: str) -> None:
        if self.is_cancelled():
            raise ValidationError(
                code="RE_CANCELLED",
                message=f"Gasto recurrente cancelado no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> RecurringExpense:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "category_id": self.category_id,
            "amount": self.amount,
            "frequency": self.frequency,
            "next_date": self.next_date,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
        }
        data.update(kwargs)
        return RecurringExpense(**data)  # type: ignore[arg-type]
