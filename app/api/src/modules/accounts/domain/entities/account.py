from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import AccountStatus, AccountType

MAX_NAME_LEN = 80


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


@dataclass(slots=True)
class Account:
    id: str
    user_id: str
    name: str
    type: AccountType = AccountType.OTHER
    currency: str = "PEN"
    initial_balance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    current_balance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    is_default: bool = False
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.name = _safe_str(self.name)
        self.currency = _safe_str(self.currency, "PEN").upper() or "PEN"
        self.type = AccountType.safe(self.type)
        self.status = AccountStatus.safe(self.status)
        self.initial_balance = Money.from_value(self.initial_balance, self.currency).amount
        self.current_balance = Money.from_value(self.current_balance, self.currency).amount

        if not self.user_id:
            raise ValidationError(code="ACCOUNT_USER_REQUIRED", message="user_id requerido")
        if not self.name:
            raise ValidationError(code="ACCOUNT_NAME_REQUIRED", message="name requerido")
        if len(self.name) > MAX_NAME_LEN:
            raise ValidationError(code="ACCOUNT_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}")
        if self.is_default not in (True, False):
            self.is_default = bool(self.is_default)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        type: AccountType | str = AccountType.OTHER,
        currency: str = "PEN",
        initial_balance: Decimal | str | float | int = Decimal("0.00"),
        is_default: bool = False,
    ) -> Account:
        now = _utcnow()
        amt = Money.from_value(initial_balance, currency or "PEN").amount
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            type=AccountType.safe(type),
            currency=currency,
            initial_balance=amt,
            current_balance=amt,
            is_default=is_default,
            status=AccountStatus.ACTIVE,
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
        type: object = AccountType.OTHER,
        currency: object = "PEN",
        initial_balance: object = Decimal("0.00"),
        current_balance: object = None,
        is_default: object = False,
        status: object = AccountStatus.ACTIVE,
        created_at: object = None,
        updated_at: object = None,
    ) -> Account:
        cur = _safe_str(currency, "PEN").upper() or "PEN"
        return cls(
            id=_safe_str(id) or str(uuid.uuid4()),
            user_id=_safe_str(user_id, ""),
            name=_safe_str(name, "Unknown"),
            type=AccountType.safe(type),
            currency=cur,
            initial_balance=Money.from_value(initial_balance, cur).amount,
            current_balance=Money.from_value(current_balance if current_balance is not None else initial_balance, cur).amount,
            is_default=bool(is_default) if is_default is not None else False,
            status=AccountStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    # ---- behavior (RN-002/003) ----
    def apply_income(self, amount: Decimal | Money) -> Account:
        if self.status == AccountStatus.ARCHIVED:
            raise BusinessRuleError(code="ACCOUNT_ARCHIVED", message="cuenta archivada no puede recibir movimientos")
        m = amount if isinstance(amount, Money) else Money.from_value(amount, self.currency)
        if not m.is_positive():
            raise ValidationError(code="AMOUNT_NOT_POSITIVE", message="income debe ser > 0")
        if m.currency != self.currency:
            raise BusinessRuleError(code="CURRENCY_MISMATCH", message="currency mismatch en income")
        return self._with_balance(self.current_balance + m.amount)

    def apply_expense(self, amount: Decimal | Money) -> Account:
        if self.status == AccountStatus.ARCHIVED:
            raise BusinessRuleError(code="ACCOUNT_ARCHIVED", message="cuenta archivada no puede registrar gastos")
        m = amount if isinstance(amount, Money) else Money.from_value(amount, self.currency)
        if not m.is_positive():
            raise ValidationError(code="AMOUNT_NOT_POSITIVE", message="expense debe ser > 0")
        if m.currency != self.currency:
            raise BusinessRuleError(code="CURRENCY_MISMATCH", message="currency mismatch en expense")
        return self._with_balance(self.current_balance - m.amount)

    def archive(self) -> Account:
        if self.status == AccountStatus.ARCHIVED:
            return self
        return self._with(status=AccountStatus.ARCHIVED)

    def rename(self, name: str) -> Account:
        n = _safe_str(name)
        if not n:
            raise ValidationError(code="ACCOUNT_NAME_REQUIRED", message="name requerido")
        return self._with(name=n)

    def _with_balance(self, new_balance: Decimal) -> Account:
        return Account(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            type=self.type,
            currency=self.currency,
            initial_balance=self.initial_balance,
            current_balance=new_balance,
            is_default=self.is_default,
            status=self.status,
            created_at=self.created_at,
            updated_at=_utcnow(),
        )

    def _with(self, **kwargs) -> Account:  # type: ignore[no-untyped-def]
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "currency": self.currency,
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "is_default": self.is_default,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Account(**data)  # type: ignore[arg-type]
