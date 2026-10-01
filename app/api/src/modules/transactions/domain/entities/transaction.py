from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.domain.value_objects.money import Money
from shared.errors import ValidationError
from shared.types.enums import TransactionSource, TransactionStatus, TransactionType

MAX_CONCEPTO_LEN = 500


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="TX_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_concepto(concepto: object) -> str:
    text = clean_str(concepto)
    if len(text) > MAX_CONCEPTO_LEN:
        raise ValidationError(
            code="TX_CONCEPTO_TOO_LONG", message=f"concepto excede {MAX_CONCEPTO_LEN}"
        )
    return text


@dataclass(slots=True, frozen=True)
class Transaction:
    id: str
    user_id: str
    account_id: str
    type: TransactionType
    amount: Decimal  # siempre positivo; signo lo da type
    currency: str = "PEN"
    transaction_date: datetime = field(default_factory=_utcnow)
    concepto: str = ""
    category_id: str = ""  # "" = sin categoria
    payment_method_id: str = ""  # "" = sin medio
    source: TransactionSource = TransactionSource.MANUAL
    status: TransactionStatus = TransactionStatus.COMPLETED
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="TX_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        account_id = clean_str(self.account_id)
        if not account_id:
            raise ValidationError(
                code="TX_ACCOUNT_REQUIRED", message="account_id requerido"
            )
        object.__setattr__(self, "account_id", account_id)
        currency = clean_str(self.currency, "PEN").upper() or "PEN"
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "concepto", _validate_concepto(self.concepto))
        object.__setattr__(self, "category_id", clean_str(self.category_id))
        object.__setattr__(self, "payment_method_id", clean_str(self.payment_method_id))
        object.__setattr__(self, "type", TransactionType.safe(self.type))
        object.__setattr__(self, "source", TransactionSource.safe(self.source))
        status = TransactionStatus.safe(self.status)
        # PENDING vive en pagos programados (debts/loans), no en el ledger:
        # el create siempre nace COMPLETED y solo se puede CANCELLED.
        if status not in (TransactionStatus.COMPLETED, TransactionStatus.CANCELLED):
            raise ValidationError(
                code="TX_STATUS_INVALID",
                message=f"status debe ser COMPLETED o CANCELLED, recibido: {self.status}",
            )
        object.__setattr__(self, "status", status)

        amount = Money.from_value(self.amount, currency).amount
        if amount <= Decimal("0.00"):
            raise ValidationError(
                code="TX_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0"
            )
        object.__setattr__(self, "amount", amount)

        if not isinstance(self.transaction_date, datetime):
            object.__setattr__(self, "transaction_date", _utcnow())

    @classmethod
    def create_expense(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: Decimal | str | float,
        currency: str = "PEN",
        concepto: str = "",
        category_id: str = "",
        payment_method_id: str = "",
        source: TransactionSource | str = TransactionSource.MANUAL,
        transaction_date: datetime | None = None,
    ) -> Transaction:
        return cls._create(
            TransactionType.EXPENSE,
            user_id,
            account_id,
            amount,
            currency,
            concepto,
            category_id,
            payment_method_id,
            source,
            transaction_date,
        )

    @classmethod
    def create_income(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: Decimal | str | float,
        currency: str = "PEN",
        concepto: str = "",
        category_id: str = "",
        payment_method_id: str = "",
        source: TransactionSource | str = TransactionSource.MANUAL,
        transaction_date: datetime | None = None,
    ) -> Transaction:
        return cls._create(
            TransactionType.INCOME,
            user_id,
            account_id,
            amount,
            currency,
            concepto,
            category_id,
            payment_method_id,
            source,
            transaction_date,
        )

    @classmethod
    def _create(
        cls,
        type: TransactionType,
        user_id: str,
        account_id: str,
        amount: object,
        currency: str,
        concepto: str,
        category_id: str,
        payment_method_id: str,
        source: object,
        transaction_date: datetime | None,
    ) -> Transaction:
        now = _utcnow()
        currency = clean_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            type=type,
            amount=Money.from_value(amount, currency).amount,
            currency=currency,
            transaction_date=transaction_date or now,
            concepto=concepto or "",
            category_id=category_id or "",
            payment_method_id=payment_method_id or "",
            source=TransactionSource.safe(source),
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        account_id: object,
        type: object,
        amount: object,
        currency: object = "PEN",
        transaction_date: object = None,
        concepto: object = "",
        category_id: object = "",
        payment_method_id: object = "",
        source: object = TransactionSource.MANUAL,
        status: object = TransactionStatus.COMPLETED,
        created_at: object = None,
        updated_at: object = None,
    ) -> Transaction:
        cur = clean_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            account_id=clean_str(account_id, ""),
            type=TransactionType.safe(type),
            # Sin monto mágico: None/0 falla en __post_init__ con TX_AMOUNT_NOT_POSITIVE.
            amount=Money.from_value(amount, cur).amount
            if amount is not None
            else Decimal("0.00"),
            currency=cur,
            transaction_date=transaction_date
            if isinstance(transaction_date, datetime)
            else _utcnow(),
            concepto=clean_str(concepto, ""),
            category_id=clean_str(category_id, ""),
            payment_method_id=clean_str(payment_method_id, ""),
            source=TransactionSource.safe(source),
            status=TransactionStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_expense(self) -> bool:
        return self.type == TransactionType.EXPENSE

    def is_income(self) -> bool:
        return self.type == TransactionType.INCOME

    def is_cancelled(self) -> bool:
        return self.status == TransactionStatus.CANCELLED

    def is_transfer_leg(self) -> bool:
        """Pata de una transferencia: solo se revierte vía el agregado Transfer."""
        return self.source == TransactionSource.TRANSFER

    def update_metadata(
        self,
        *,
        concepto: str | None = None,
        category_id: str | None = None,
        payment_method_id: str | None = None,
    ) -> Transaction:
        """Solo metadatos: amount/type/account_id son inmutables (integridad del ledger)."""
        self._ensure_mutable("editarse")
        return self._with(
            concepto=_validate_concepto(concepto)
            if concepto is not None
            else self.concepto,
            category_id=clean_str(category_id)
            if category_id is not None
            else self.category_id,
            payment_method_id=clean_str(payment_method_id)
            if payment_method_id is not None
            else self.payment_method_id,
        )

    def cancel(self) -> Transaction:
        if self.is_transfer_leg():
            raise ValidationError(
                code="TX_TRANSFER_LEG",
                message="Pata de transferencia no puede cancelarse directamente.",
            )
        if self.is_cancelled():
            return self
        return self._with(status=TransactionStatus.CANCELLED)

    def mark_leg_reversed(self) -> Transaction:
        """Marca una pata de transferencia como revertida (solo vía reverse_transfer)."""
        if not self.is_transfer_leg():
            raise ValidationError(
                code="TX_NOT_TRANSFER_LEG",
                message="Solo patas de transferencia pueden marcarse como revertidas.",
            )
        if self.is_cancelled():
            return self
        return self._with(status=TransactionStatus.CANCELLED)

    def _ensure_mutable(self, action: str) -> None:
        if self.status == TransactionStatus.CANCELLED:
            raise ValidationError(
                code="TX_ALREADY_CANCELLED",
                message=f"Transacción cancelada no puede {action}.",
            )
        if self.is_transfer_leg():
            raise ValidationError(
                code="TX_TRANSFER_LEG",
                message=f"Pata de transferencia no puede {action} directamente.",
            )

    def _with(self, **kwargs: object) -> Transaction:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "type": self.type,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_date": self.transaction_date,
            "concepto": self.concepto,
            "category_id": self.category_id,
            "payment_method_id": self.payment_method_id,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Transaction(**data)  # type: ignore[arg-type]
