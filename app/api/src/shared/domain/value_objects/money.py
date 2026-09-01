"""Todo en el dominio de negocio que represente un importe monetario debe usar este Value Object."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from shared.errors import ValidationError

_MAX_AMOUNT = Decimal("999999999999.99")
_MIN_AMOUNT = Decimal("0.00")
_QUANTIZE = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    """Value object para importes monetarios.

    - Siempre Decimal con 2 decimales.
    - Nunca None: usa Decimal("0.00") como default.
    """

    amount: Decimal
    currency: str = "PEN"

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency", (self.currency or "PEN").upper().strip() or "PEN")
        amt = self._coerce(self.amount)
        if amt.is_nan() or amt.is_infinite():
            amt = Decimal("0.00")
        if amt < _MIN_AMOUNT:
            raise ValidationError(code="MONEY_NEGATIVE", message=f"amount no puede ser negativo: {amt}")
        if amt > _MAX_AMOUNT:
            raise ValidationError(code="MONEY_TOO_LARGE", message=f"amount excede máximo permitido: {amt}")
        # Cuantiza a 2 decimales
        quantized = amt.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)

    @staticmethod
    def _coerce(value: object) -> Decimal:
        def _guard(d: Decimal) -> Decimal:
            try:
                if d.is_nan() or d.is_infinite():
                    return Decimal("0.00")
            except AttributeError:
                pass
            return d

        if value is None:
            return Decimal("0.00")
        if isinstance(value, Decimal):
            return _guard(value)
        if isinstance(value, (int, float)):
            try:
                return _guard(Decimal(str(value)))
            except (InvalidOperation, ValueError, TypeError):
                return Decimal("0.00")
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return Decimal("0.00")
            try:
                return _guard(Decimal(v))
            except (InvalidOperation, ValueError):
                return Decimal("0.00")
        return Decimal("0.00")

    @classmethod
    def zero(cls, currency: str = "PEN") -> Money:
        return cls(amount=Decimal("0.00"), currency=currency)

    @classmethod
    def from_value(cls, value: object, currency: str = "PEN") -> Money:
        """Crea Money desde cualquier tipo; si es inválido retorna 0.00."""
        try:
            return cls(amount=cls._coerce(value), currency=currency)
        except ValidationError:
            return cls.zero(currency)

    def add(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def is_zero(self) -> bool:
        return self.amount == Decimal("0.00")

    def is_positive(self) -> bool:
        return self.amount > Decimal("0.00")

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise BusinessRuleError(code="CURRENCY_MISMATCH", message=f"currency mismatch {self.currency} vs {other.currency}")  # type: ignore[name-defined]

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


# Local import at end to avoid circular
from shared.errors import BusinessRuleError
