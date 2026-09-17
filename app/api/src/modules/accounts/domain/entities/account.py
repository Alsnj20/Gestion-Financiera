from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from shared.domain.guards import clean_str as _clean_str
from shared.domain.guards import shadow_name as _shadow_name
from shared.domain.guards import utcnow as _utcnow
from shared.domain.guards import validate_bool as _validate_bool
from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import AccountStatus, AccountType

MAX_NAME_LEN = 80


# ---- Helper functions ----
def _validate_name(name: str) -> str:
    name = _clean_str(name)
    if not name:
        raise ValidationError(code="ACCOUNT_NAME_REQUIRED", message="name requerido")
    if len(name) > MAX_NAME_LEN:
        raise ValidationError(
            code="ACCOUNT_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}"
        )
    return name


@dataclass(slots=True, frozen=True)
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
        """Normalization and validation of fields after initialization"""

        object.__setattr__(self, "id", _clean_str(self.id))
        object.__setattr__(self, "user_id", _clean_str(self.user_id))
        object.__setattr__(self, "name", _clean_str(self.name))
        currency = _clean_str(self.currency, "PEN").upper()
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "type", AccountType.safe(self.type))
        object.__setattr__(self, "status", AccountStatus.safe(self.status))
        object.__setattr__(
            self, "is_default", _validate_bool(self.is_default, "is_default")
        )

        if not self.id:
            raise ValidationError(code="ACCOUNT_ID_REQUIRED", message="id requerido")
        if not self.user_id:
            raise ValidationError(
                code="ACCOUNT_USER_REQUIRED", message="user_id requerido"
            )

        validated_name = _validate_name(self.name)
        object.__setattr__(self, "name", validated_name)

        if not currency:
            raise ValidationError(
                code="ACCOUNT_CURRENCY_REQUIRED", message="currency requerido"
            )

        # Money - Decimal consistency
        initial_money = Money.from_value(self.initial_balance, currency)
        current_money = Money.from_value(self.current_balance, currency)

        object.__setattr__(self, "initial_balance", initial_money.amount)
        object.__setattr__(self, "current_balance", current_money.amount)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        type: AccountType | str = AccountType.OTHER,
        currency: str = "PEN",
        initial_balance: Decimal | str | float = Decimal("0.00"),
        is_default: bool = False,
    ) -> Account:
        now = _utcnow()
        clean_currency = _clean_str(currency, "PEN").upper()
        amount = Money.from_value(initial_balance, clean_currency).amount

        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            type=AccountType.safe(type),
            currency=clean_currency,
            initial_balance=amount,
            current_balance=amount,
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

        clean_id = _clean_str(id)
        if not clean_id:
            raise ValidationError(code="ACCOUNT_ID_REQUIRED", message="id requerido")

        clean_currency = _clean_str(currency, "PEN").upper()
        initial_amount = Money.from_value(initial_balance, clean_currency).amount

        if current_balance is None:
            current_amount = initial_amount
        else:
            current_amount = Money.from_value(current_balance, clean_currency).amount

        is_default = _validate_bool(is_default, "is_default")

        return cls(
            id=clean_id,
            user_id=_clean_str(user_id),
            name=_clean_str(name),
            type=AccountType.safe(type),
            currency=clean_currency,
            initial_balance=initial_amount,
            current_balance=current_amount,
            is_default=is_default,
            status=AccountStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    # ---- domain behavior (RN-002/003) ----
    def apply_income(self, amount: Decimal | Money) -> Account:
        """Apply an income to the account, returning a new Account instance with updated balance."""

        self._ensure_active("recibir movimientos")
        money = (
            amount
            if isinstance(amount, Money)
            else Money.from_value(amount, self.currency)
        )

        self._validate_amount(money, "income")

        return self._with_balance(self.current_balance + money.amount)

    def apply_expense(self, amount: Decimal | Money) -> Account:
        """Apply an expense to the account, returning a new Account instance with updated balance."""

        self._ensure_active("realizar gastos")
        money = (
            amount
            if isinstance(amount, Money)
            else Money.from_value(amount, self.currency)
        )
        self._validate_amount(money, "expense")

        return self._with_balance(self.current_balance - money.amount)

    def archive(self) -> Account:
        if self.status == AccountStatus.ARCHIVED:
            return self
        return self._with(status=AccountStatus.ARCHIVED)

    def rename(self, name: str) -> Account:
        self._ensure_active("editarse")
        validated_name = _validate_name(name)
        return self._with(name=validated_name)

    # ---- domain helpers ----
    def _ensure_active(self, action_description: str) -> None:
        if self.status == AccountStatus.ARCHIVED:
            raise BusinessRuleError(
                code="ACCOUNT_ARCHIVED",
                message=f"Cuenta archivada no puede {action_description}.",
            )

    def _validate_amount(self, money: Money, action_type: str) -> None:
        if not money.is_positive():
            raise ValidationError(
                code=f"ACCOUNT_{action_type.upper()}_NEGATIVE",
                message=f"{action_type.capitalize()} debe ser positivo.",
            )

        if money.currency != self.currency:
            raise BusinessRuleError(
                code=f"ACCOUNT_{action_type.upper()}_CURRENCY_MISMATCH",
                message=f"{action_type.capitalize()} debe ser en la misma moneda que la cuenta.",
            )

    def _with_balance(self, new_balance: Decimal) -> Account:
        return self._with(current_balance=new_balance)

    def _with(self, **kwargs: object) -> Account:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
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

    def mark_as_default(self) -> Account:
        self._ensure_active("marcarse como default")
        return self._with(is_default=True)

    def unmark_as_default(self) -> Account:
        return self._with(is_default=False)

    def archive_with_shadow_name(self) -> Account:
        """Borrado lógico visible: archiva, desmarca default y renombra a
        '{nombre}_deleted_{id8}' para liberar el nombre original."""
        shadowed = _shadow_name(self.name, self.id, MAX_NAME_LEN, fallback="cuenta")
        return self.archive()._with(name=shadowed, is_default=False)

    def restore(self, name: str) -> Account:
        if self.status != AccountStatus.ARCHIVED:
            raise BusinessRuleError(
                code="ACCOUNT_NOT_ARCHIVED",
                message="Solo se puede restaurar una cuenta archivada.",
            )
        return self._with(name=_validate_name(name), status=AccountStatus.ACTIVE)

    def change_type(self, account_type: AccountType | str) -> Account:
        self._ensure_active("editarse")
        return self._with(type=AccountType.safe(account_type))
