from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import TransferStatus

MAX_DESC_LEN = 500


def _validate_description(description: object) -> str:
    text = clean_str(description)
    if len(text) > MAX_DESC_LEN:
        raise ValidationError(
            code="TR_DESC_TOO_LONG", message=f"description excede {MAX_DESC_LEN}"
        )
    return text


@dataclass(slots=True, frozen=True)
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
    status: TransferStatus = TransferStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        transfer_id = clean_str(self.id)
        if not transfer_id:
            raise ValidationError(code="TR_ID_REQUIRED", message="id requerido")
        object.__setattr__(self, "id", transfer_id)
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="TR_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        source_account_id = clean_str(self.source_account_id)
        destination_account_id = clean_str(self.destination_account_id)
        if not source_account_id or not destination_account_id:
            raise ValidationError(
                code="TR_ACCOUNT_REQUIRED",
                message="cuentas origen y destino requeridas",
            )
        object.__setattr__(self, "source_account_id", source_account_id)
        object.__setattr__(self, "destination_account_id", destination_account_id)
        if source_account_id == destination_account_id:
            raise BusinessRuleError(
                code="TR_SAME_ACCOUNT",
                message="origen y destino no pueden ser la misma cuenta",
            )
        object.__setattr__(
            self, "source_transaction_id", clean_str(self.source_transaction_id)
        )
        object.__setattr__(
            self,
            "destination_transaction_id",
            clean_str(self.destination_transaction_id),
        )
        currency = clean_str(self.currency, "PEN").upper() or "PEN"
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "description", _validate_description(self.description))
        amount = Money.from_value(self.amount, currency).amount
        if amount <= Decimal("0.00"):
            raise ValidationError(
                code="TR_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
            )
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "status", TransferStatus.safe(self.status))
        if not isinstance(self.date, datetime):
            object.__setattr__(self, "date", _utcnow())

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        source_account_id: str,
        destination_account_id: str,
        source_transaction_id: str,
        destination_transaction_id: str,
        amount: Decimal | str | float,
        currency: str = "PEN",
        description: str = "",
        date: datetime | None = None,
    ) -> Transfer:
        now = _utcnow()
        currency = clean_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            source_transaction_id=source_transaction_id,
            destination_transaction_id=destination_transaction_id,
            amount=Money.from_value(amount, currency).amount,
            currency=currency,
            date=date or now,
            description=description or "",
            status=TransferStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        source_account_id: object,
        destination_account_id: object,
        source_transaction_id: object,
        destination_transaction_id: object,
        amount: object,
        currency: object = "PEN",
        date: object = None,
        description: object = "",
        status: object = TransferStatus.ACTIVE,
        created_at: object = None,
        updated_at: object = None,
    ) -> Transfer:
        cur = clean_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            source_account_id=clean_str(source_account_id, ""),
            destination_account_id=clean_str(destination_account_id, ""),
            source_transaction_id=clean_str(source_transaction_id, ""),
            destination_transaction_id=clean_str(destination_transaction_id, ""),
            # Sin monto mágico: None/0 falla en __post_init__ con TR_AMOUNT_NOT_POSITIVE.
            amount=Money.from_value(amount, cur).amount
            if amount is not None
            else Decimal("0.00"),
            currency=cur,
            date=date if isinstance(date, datetime) else _utcnow(),
            description=clean_str(description, ""),
            status=TransferStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_reversed(self) -> bool:
        return self.status == TransferStatus.REVERSED

    def mark_reversed(self) -> Transfer:
        """Reversión lógica: el agregado se conserva como REVERSED, nunca se borra."""
        if self.is_reversed():
            return self
        return self._with(status=TransferStatus.REVERSED)

    def _with(self, **kwargs: object) -> Transfer:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "source_account_id": self.source_account_id,
            "destination_account_id": self.destination_account_id,
            "source_transaction_id": self.source_transaction_id,
            "destination_transaction_id": self.destination_transaction_id,
            "amount": self.amount,
            "currency": self.currency,
            "date": self.date,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Transfer(**data)  # type: ignore[arg-type]
