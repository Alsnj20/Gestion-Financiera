from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.errors import ValidationError
from shared.types.enums import TransactionSource, TransactionStatus, TransactionType

MAX_DESC_LEN = 500


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class Transaction:
    id: str
    user_id: str
    account_id: str
    type: TransactionType
    amount: Decimal  # siempre positivo; signo lo da type
    currency: str = "PEN"
    transaction_date: datetime = field(default_factory=_utcnow)
    description: str = ""
    category_id: str = ""  # "" = sin categoria
    payment_method_id: str = ""  # "" = sin medio
    source: TransactionSource = TransactionSource.MANUAL
    status: TransactionStatus = TransactionStatus.COMPLETED
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.account_id = _safe_str(self.account_id)
        self.currency = _safe_str(self.currency, "PEN").upper() or "PEN"
        self.description = _safe_str(self.description, "")
        self.category_id = _safe_str(self.category_id, "")
        self.payment_method_id = _safe_str(self.payment_method_id, "")
        self.type = TransactionType.safe(self.type)
        self.source = TransactionSource.safe(self.source)
        self.status = TransactionStatus.safe(self.status)

        self.amount = Money.from_value(self.amount, self.currency).amount
        if self.amount <= Decimal("0.00"):
            raise ValidationError(code="TX_AMOUNT_NOT_POSITIVE", message="amount debe ser > 0")
        if len(self.description) > MAX_DESC_LEN:
            raise ValidationError(code="TX_DESC_TOO_LONG", message=f"description excede {MAX_DESC_LEN}")

        if not self.user_id:
            raise ValidationError(code="TX_USER_REQUIRED", message="user_id requerido")
        if not self.account_id:
            raise ValidationError(code="TX_ACCOUNT_REQUIRED", message="account_id requerido")
        if not isinstance(self.transaction_date, datetime):
            self.transaction_date = _utcnow()

    @classmethod
    def create_expense(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: Decimal | str | float | int,
        currency: str = "PEN",
        description: str = "",
        category_id: str = "",
        payment_method_id: str = "",
        source: TransactionSource | str = TransactionSource.MANUAL,
        transaction_date: datetime | None = None,
    ) -> Transaction:
        return cls._create(TransactionType.EXPENSE, user_id, account_id, amount, currency, description, category_id, payment_method_id, source, transaction_date)

    @classmethod
    def create_income(
        cls,
        *,
        user_id: str,
        account_id: str,
        amount: Decimal | str | float | int,
        currency: str = "PEN",
        description: str = "",
        category_id: str = "",
        payment_method_id: str = "",
        source: TransactionSource | str = TransactionSource.MANUAL,
        transaction_date: datetime | None = None,
    ) -> Transaction:
        return cls._create(TransactionType.INCOME, user_id, account_id, amount, currency, description, category_id, payment_method_id, source, transaction_date)

    @classmethod
    def _create(cls, type: TransactionType, user_id: str, account_id: str, amount: object, currency: str, description: str, category_id: str, payment_method_id: str, source: object, transaction_date: datetime | None) -> Transaction:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            type=type,
            amount=Money.from_value(amount, currency or "PEN").amount,
            currency=currency or "PEN",
            transaction_date=transaction_date or now,
            description=description or "",
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
        description: object = "",
        category_id: object = "",
        payment_method_id: object = "",
        source: object = TransactionSource.MANUAL,
        status: object = TransactionStatus.COMPLETED,
        created_at: object = None,
        updated_at: object = None,
    ) -> Transaction:
        cur = _safe_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=_safe_str(id) or str(uuid.uuid4()),
            user_id=_safe_str(user_id, ""),
            account_id=_safe_str(account_id, ""),
            type=TransactionType.safe(type),
            amount=Money.from_value(amount, cur).amount if amount is not None else Decimal("0.01"),
            currency=cur,
            transaction_date=transaction_date if isinstance(transaction_date, datetime) else _utcnow(),
            description=_safe_str(description, "")[:MAX_DESC_LEN],
            category_id=_safe_str(category_id, ""),
            payment_method_id=_safe_str(payment_method_id, ""),
            source=TransactionSource.safe(source),
            status=TransactionStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_expense(self) -> bool:
        return self.type == TransactionType.EXPENSE

    def is_income(self) -> bool:
        return self.type == TransactionType.INCOME

    def cancel(self) -> Transaction:
        if self.status == TransactionStatus.CANCELLED:
            return self
        return Transaction(
            id=self.id, user_id=self.user_id, account_id=self.account_id, type=self.type, amount=self.amount, currency=self.currency,
            transaction_date=self.transaction_date, description=self.description, category_id=self.category_id, payment_method_id=self.payment_method_id,
            source=self.source, status=TransactionStatus.CANCELLED, created_at=self.created_at, updated_at=_utcnow(),
        )
