from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError

MAX_DESC_LEN = 500


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class Transfer:
    """RN-001: transferencia no es ingreso ni gasto. Se modela como 2 Transactions + este agregado."""

    id: str
    user_id: str
    source_account_id: str
    destination_account_id: str
    source_transaction_id: str
    destination_transaction_id: str
    amount: Decimal
    currency: str = "PEN"
    date: datetime = field(default_factory=_utcnow)
    description: str = ""
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.source_account_id = _safe_str(self.source_account_id)
        self.destination_account_id = _safe_str(self.destination_account_id)
        self.source_transaction_id = _safe_str(self.source_transaction_id)
        self.destination_transaction_id = _safe_str(self.destination_transaction_id)
        self.currency = _safe_str(self.currency, "PEN").upper() or "PEN"
        self.description = _safe_str(self.description, "")[:MAX_DESC_LEN]
        self.amount = Money.from_value(self.amount, self.currency).amount

        if not self.user_id:
            raise ValidationError(code="TR_USER_REQUIRED", message="user_id requerido")
        if not self.source_account_id or not self.destination_account_id:
            raise ValidationError(code="TR_ACCOUNT_REQUIRED", message="cuentas origen y destino requeridas")
        if self.source_account_id == self.destination_account_id:
            raise BusinessRuleError(code="TR_SAME_ACCOUNT", message="origen y destino no pueden ser la misma cuenta")
        if self.amount <= Decimal("0.00"):
            raise ValidationError(code="TR_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0")
        if not isinstance(self.date, datetime):
            self.date = _utcnow()

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        source_account_id: str,
        destination_account_id: str,
        source_transaction_id: str,
        destination_transaction_id: str,
        amount: Decimal | str | float | int,
        currency: str = "PEN",
        description: str = "",
        date: datetime | None = None,
    ) -> Transfer:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            source_transaction_id=source_transaction_id,
            destination_transaction_id=destination_transaction_id,
            amount=Money.from_value(amount, currency or "PEN").amount,
            currency=currency or "PEN",
            date=date or now,
            description=description or "",
            created_at=now,
        )

    @classmethod
    def rehydrate(cls, *, id: object, user_id: object, source_account_id: object, destination_account_id: object, source_transaction_id: object, destination_transaction_id: object, amount: object, currency: object = "PEN", date: object = None, description: object = "", created_at: object = None) -> Transfer:
        cur = _safe_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=_safe_str(id) or str(uuid.uuid4()),
            user_id=_safe_str(user_id, ""),
            source_account_id=_safe_str(source_account_id, ""),
            destination_account_id=_safe_str(destination_account_id, ""),
            source_transaction_id=_safe_str(source_transaction_id, ""),
            destination_transaction_id=_safe_str(destination_transaction_id, ""),
            amount=Money.from_value(amount, cur).amount if amount is not None else Decimal("0.01"),
            currency=cur,
            date=date if isinstance(date, datetime) else _utcnow(),
            description=_safe_str(description, "")[:MAX_DESC_LEN],
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
        )
