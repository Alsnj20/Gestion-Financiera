from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from shared.domain.guards import clean_str, safe_date
from shared.domain.guards import utcnow as _utcnow
from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import BudgetStatus

MAX_NAME_LEN = 120


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="BUDGET_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_name(name: object) -> str:
    text = clean_str(name)
    if not text:
        raise ValidationError(code="BUDGET_NAME_REQUIRED", message="name requerido")
    if len(text) > MAX_NAME_LEN:
        raise ValidationError(
            code="BUDGET_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}"
        )
    return text


def _validate_amount(amount: object) -> Decimal:
    value = Money.from_value(amount).amount
    if value <= Decimal("0.00"):
        raise ValidationError(
            code="BUDGET_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
        )
    return value


@dataclass(slots=True, frozen=True)
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
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(
                code="BUDGET_USER_REQUIRED", message="user_id requerido"
            )
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "name", _validate_name(self.name))
        object.__setattr__(self, "category_id", clean_str(self.category_id))
        object.__setattr__(self, "status", BudgetStatus.safe(self.status))
        object.__setattr__(self, "amount", _validate_amount(self.amount))
        period_start = safe_date(self.period_start)
        period_end = safe_date(self.period_end)
        if period_end < period_start:
            raise ValidationError(
                code="BUDGET_PERIOD_INVALID",
                message="period_end no puede ser anterior a period_start",
            )
        object.__setattr__(self, "period_start", period_start)
        object.__setattr__(self, "period_end", period_end)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        amount: Decimal,
        period_start: date,
        period_end: date,
        category_id: str = "",
    ) -> Budget:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            amount=amount,
            period_start=period_start,
            period_end=period_end,
            category_id=category_id or "",
            status=BudgetStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        name: object,
        amount: object,
        period_start: object = None,
        period_end: object = None,
        category_id: object = "",
        status: object = BudgetStatus.ACTIVE,
        created_at: object = None,
        updated_at: object = None,
    ) -> Budget:
        # Sin monto mágico: None/0 falla en __post_init__ con BUDGET_AMOUNT_NOT_POSITIVE.
        value = (
            Money.from_value(amount).amount if amount is not None else Decimal("0.00")
        )
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            name=clean_str(name, ""),
            amount=value,
            period_start=safe_date(period_start),
            period_end=safe_date(period_end),
            category_id=clean_str(category_id, ""),
            status=BudgetStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_archived(self) -> bool:
        return self.status == BudgetStatus.ARCHIVED

    def archive(self) -> Budget:
        if self.is_archived():
            return self
        return self._with(status=BudgetStatus.ARCHIVED)

    def restore(self) -> Budget:
        if not self.is_archived():
            raise BusinessRuleError(
                code="BUDGET_NOT_ARCHIVED",
                message="Solo se puede restaurar un presupuesto archivado.",
            )
        return self._with(status=BudgetStatus.ACTIVE)

    def update_details(
        self,
        *,
        name: str | None = None,
        amount: Decimal | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        category_id: str | None = None,
    ) -> Budget:
        self._ensure_active("editarse")
        new_start = (
            safe_date(period_start, self.period_start)
            if period_start is not None
            else self.period_start
        )
        new_end = (
            safe_date(period_end, self.period_end)
            if period_end is not None
            else self.period_end
        )
        if new_end < new_start:
            raise ValidationError(
                code="BUDGET_PERIOD_INVALID",
                message="period_end no puede ser anterior a period_start",
            )
        return self._with(
            name=_validate_name(name) if name is not None else self.name,
            amount=_validate_amount(amount) if amount is not None else self.amount,
            period_start=new_start,
            period_end=new_end,
            category_id=clean_str(category_id)
            if category_id is not None
            else self.category_id,
        )

    def _ensure_active(self, action_description: str) -> None:
        if self.is_archived():
            raise BusinessRuleError(
                code="BUDGET_ARCHIVED",
                message=f"Presupuesto archivado no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> Budget:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "category_id": self.category_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Budget(**data)  # type: ignore[arg-type]
