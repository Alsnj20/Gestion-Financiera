from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import BudgetStatus, PeriodType

MAX_NAME_LEN = 120


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="LIMIT_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_name(name: object) -> str:
    text = clean_str(name)
    if not text:
        raise ValidationError(code="LIMIT_NAME_REQUIRED", message="name requerido")
    if len(text) > MAX_NAME_LEN:
        raise ValidationError(
            code="LIMIT_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}"
        )
    return text


def _validate_threshold(value: object) -> Decimal:
    try:
        threshold = Decimal(str(value)) if value is not None else Decimal(80)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(
            code="LIMIT_THRESHOLD_INVALID", message="threshold_warning inválido"
        )
    if threshold < Decimal(0) or threshold > Decimal(100):
        raise ValidationError(
            code="LIMIT_THRESHOLD_OUT_OF_RANGE",
            message="threshold_warning debe estar entre 0 y 100",
        )
    return threshold


@dataclass(slots=True, frozen=True)
class Limit:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_type: PeriodType = PeriodType.MONTHLY
    category_id: str = ""
    threshold_warning: Decimal = Decimal(80)
    status: BudgetStatus = BudgetStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(
                code="LIMIT_USER_REQUIRED", message="user_id requerido"
            )
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "name", _validate_name(self.name))
        object.__setattr__(self, "category_id", clean_str(self.category_id))
        object.__setattr__(self, "period_type", PeriodType.safe(self.period_type))
        object.__setattr__(self, "status", BudgetStatus.safe(self.status))
        amount = Money.from_value(self.amount).amount
        if amount <= Decimal("0.00"):
            raise ValidationError(
                code="LIMIT_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
            )
        object.__setattr__(self, "amount", amount)
        object.__setattr__(
            self, "threshold_warning", _validate_threshold(self.threshold_warning)
        )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        amount: Decimal | str | float,
        period_type: PeriodType | str = PeriodType.MONTHLY,
        category_id: str = "",
        threshold_warning: Decimal | str | float = Decimal(80),
    ) -> Limit:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            amount=amount,
            period_type=PeriodType.safe(period_type),
            category_id=category_id or "",
            threshold_warning=threshold_warning,
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
        period_type: object = PeriodType.MONTHLY,
        category_id: object = "",
        threshold_warning: object = Decimal(80),
        status: object = BudgetStatus.ACTIVE,
        created_at: object = None,
        updated_at: object = None,
    ) -> Limit:
        # Sin monto mágico: None/0 falla en __post_init__ con LIMIT_AMOUNT_NOT_POSITIVE.
        value = (
            Money.from_value(amount).amount if amount is not None else Decimal("0.00")
        )
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            name=clean_str(name, ""),
            amount=value,
            period_type=PeriodType.safe(period_type),
            category_id=clean_str(category_id, ""),
            threshold_warning=threshold_warning,
            status=BudgetStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_archived(self) -> bool:
        return self.status == BudgetStatus.ARCHIVED

    def archive(self) -> Limit:
        if self.is_archived():
            return self
        return self._with(status=BudgetStatus.ARCHIVED)

    def restore(self) -> Limit:
        if not self.is_archived():
            raise BusinessRuleError(
                code="LIMIT_NOT_ARCHIVED",
                message="Solo se puede restaurar un límite archivado.",
            )
        return self._with(status=BudgetStatus.ACTIVE)

    def update_details(
        self,
        *,
        name: str | None = None,
        amount: Decimal | None = None,
        period_type: PeriodType | str | None = None,
        category_id: str | None = None,
        threshold_warning: Decimal | None = None,
    ) -> Limit:
        self._ensure_active("editarse")
        if amount is not None:
            value = Money.from_value(amount).amount
            if value <= Decimal("0.00"):
                raise ValidationError(
                    code="LIMIT_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
                )
        else:
            value = self.amount
        return self._with(
            name=_validate_name(name) if name is not None else self.name,
            amount=value,
            period_type=PeriodType.safe(period_type)
            if period_type is not None
            else self.period_type,
            category_id=clean_str(category_id)
            if category_id is not None
            else self.category_id,
            threshold_warning=_validate_threshold(threshold_warning)
            if threshold_warning is not None
            else self.threshold_warning,
        )

    def _ensure_active(self, action_description: str) -> None:
        if self.is_archived():
            raise BusinessRuleError(
                code="LIMIT_ARCHIVED",
                message=f"Límite archivado no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> Limit:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "period_type": self.period_type,
            "category_id": self.category_id,
            "threshold_warning": self.threshold_warning,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Limit(**data)  # type: ignore[arg-type]
