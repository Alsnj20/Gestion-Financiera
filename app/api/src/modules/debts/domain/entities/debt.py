from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from shared.domain.guards import clean_str, safe_date, today
from shared.domain.guards import utcnow as _utcnow
from shared.domain.schedule import build_schedule
from shared.domain.schedule import total_interest as _total_interest
from shared.domain.value_objects.money import Money
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import (
    AmortizationMethod,
    InstallmentStatus,
    InterestRateType,
    LoanStatus,
    PaymentFrequency,
)

MAX_NAME_LEN = 120
MAX_NOTES_LEN = 1000


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="DEBT_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_name(name: object) -> str:
    text = clean_str(name)
    if not text:
        raise ValidationError(
            code="DEBT_CREDITOR_REQUIRED", message="creditor_name requerido"
        )
    if len(text) > MAX_NAME_LEN:
        raise ValidationError(
            code="DEBT_CREDITOR_TOO_LONG",
            message=f"creditor_name excede {MAX_NAME_LEN}",
        )
    return text


def _validate_notes(notes: object) -> str:
    text = clean_str(notes)
    if len(text) > MAX_NOTES_LEN:
        raise ValidationError(
            code="DEBT_NOTES_TOO_LONG", message=f"notes excede {MAX_NOTES_LEN}"
        )
    return text


def _validate_rate(rate: object) -> Decimal:
    # Money.from_value convierte negativos en 0: validar el crudo primero.
    try:
        raw = Decimal(str(rate))
    except (InvalidOperation, ValueError, TypeError):
        raw = Decimal("0.00")
    if raw < Decimal("0.00"):
        raise ValidationError(
            code="DEBT_RATE_NEGATIVE", message="interest_rate no puede ser negativo"
        )
    return Money.from_value(rate).amount


@dataclass(slots=True, frozen=True)
class DebtInstallment:
    id: str
    debt_id: str
    installment_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    principal_paid: Decimal = Decimal("0.00")
    interest_paid: Decimal = Decimal("0.00")
    status: InstallmentStatus = InstallmentStatus.PENDING
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        object.__setattr__(self, "debt_id", clean_str(self.debt_id))
        object.__setattr__(self, "status", InstallmentStatus.safe(self.status))
        number = (
            int(self.installment_number) if self.installment_number is not None else 1
        )
        object.__setattr__(self, "installment_number", max(number, 1))
        object.__setattr__(self, "due_date", safe_date(self.due_date))
        object.__setattr__(
            self, "principal_due", Money.from_value(self.principal_due).amount
        )
        object.__setattr__(
            self, "interest_due", Money.from_value(self.interest_due).amount
        )
        total = (
            Money.from_value(self.total_due).amount
            if self.total_due is not None
            else self.principal_due + self.interest_due
        )
        object.__setattr__(self, "total_due", total)
        object.__setattr__(
            self, "principal_paid", Money.from_value(self.principal_paid).amount
        )
        object.__setattr__(
            self, "interest_paid", Money.from_value(self.interest_paid).amount
        )

    @property
    def is_paid(self) -> bool:
        return self.status == InstallmentStatus.PAID

    def apply_payment(self, principal: Decimal, interest: Decimal) -> DebtInstallment:
        p = Money.from_value(principal).amount
        i = Money.from_value(interest).amount
        new_p_paid = min(self.principal_due, self.principal_paid + p)
        new_i_paid = min(self.interest_due, self.interest_paid + i)
        fully_paid = (
            new_p_paid >= self.principal_due and new_i_paid >= self.interest_due
        )
        partially = (
            new_p_paid > Decimal("0.00") or new_i_paid > Decimal("0.00")
        ) and not fully_paid
        if fully_paid:
            status = InstallmentStatus.PAID
        elif partially:
            status = InstallmentStatus.PARTIAL
        else:
            status = self.status
        return self._with(
            principal_paid=new_p_paid, interest_paid=new_i_paid, status=status
        )

    def mark_overdue_if_needed(self, ref_date: date | None = None) -> DebtInstallment:
        t = ref_date or today()
        if self.status in (InstallmentStatus.PAID, InstallmentStatus.CANCELLED):
            return self
        if self.due_date < t:
            return self._with(status=InstallmentStatus.OVERDUE)
        return self

    def _with(self, **kwargs: object) -> DebtInstallment:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "debt_id": self.debt_id,
            "installment_number": self.installment_number,
            "due_date": self.due_date,
            "principal_due": self.principal_due,
            "interest_due": self.interest_due,
            "total_due": self.total_due,
            "principal_paid": self.principal_paid,
            "interest_paid": self.interest_paid,
            "status": self.status,
            "created_at": self.created_at,
        }
        data.update(kwargs)
        return DebtInstallment(**data)  # type: ignore[arg-type]


@dataclass(slots=True, frozen=True)
class DebtPayment:
    id: str
    debt_id: str
    transaction_id: str
    payment_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    installment_id: str = ""  # vacío = sin cuota vinculada
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        object.__setattr__(self, "debt_id", clean_str(self.debt_id))
        object.__setattr__(self, "transaction_id", clean_str(self.transaction_id))
        object.__setattr__(self, "installment_id", clean_str(self.installment_id))
        object.__setattr__(self, "payment_date", safe_date(self.payment_date))
        object.__setattr__(
            self, "principal_amount", Money.from_value(self.principal_amount).amount
        )
        object.__setattr__(
            self, "interest_amount", Money.from_value(self.interest_amount).amount
        )
        total = (
            Money.from_value(self.total_amount).amount
            if self.total_amount is not None
            else self.principal_amount + self.interest_amount
        )
        object.__setattr__(self, "total_amount", total)


@dataclass(slots=True, frozen=True)
class Debt:
    id: str
    user_id: str
    creditor_name: str
    principal_amount: Decimal
    interest_rate: Decimal = Decimal("0.00")
    interest_rate_type: InterestRateType = InterestRateType.PERCENTAGE
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    installment_count: int = 1
    installment_amount: Decimal = Decimal("0.00")
    start_date: date = field(default_factory=today)
    first_due_date: date = field(default_factory=today)
    amortization_method: AmortizationMethod = AmortizationMethod.SIMPLE
    status: LoanStatus = LoanStatus.ACTIVE
    notes: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(
                code="DEBT_USER_REQUIRED", message="user_id requerido"
            )
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "creditor_name", _validate_name(self.creditor_name))
        object.__setattr__(self, "notes", _validate_notes(self.notes))
        object.__setattr__(
            self, "interest_rate_type", InterestRateType.safe(self.interest_rate_type)
        )
        object.__setattr__(
            self, "payment_frequency", PaymentFrequency.safe(self.payment_frequency)
        )
        object.__setattr__(
            self,
            "amortization_method",
            AmortizationMethod.safe(self.amortization_method),
        )
        object.__setattr__(self, "status", LoanStatus.safe(self.status))
        principal = Money.from_value(self.principal_amount).amount
        if principal <= Decimal("0.00"):
            raise ValidationError(
                code="DEBT_PRINCIPAL_NOT_POSITIVE",
                message="principal_amount debe ser > 0",
            )
        object.__setattr__(self, "principal_amount", principal)
        object.__setattr__(self, "interest_rate", _validate_rate(self.interest_rate))
        object.__setattr__(
            self, "installment_amount", Money.from_value(self.installment_amount).amount
        )
        count = int(self.installment_count) if self.installment_count is not None else 1
        object.__setattr__(self, "installment_count", max(count, 1))
        object.__setattr__(self, "start_date", safe_date(self.start_date))
        object.__setattr__(self, "first_due_date", safe_date(self.first_due_date))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        creditor_name: str,
        principal_amount: Decimal | str | float,
        interest_rate: Decimal | str | float = Decimal("0.00"),
        interest_rate_type: InterestRateType | str = InterestRateType.PERCENTAGE,
        payment_frequency: PaymentFrequency | str = PaymentFrequency.MONTHLY,
        installment_count: int = 1,
        installment_amount: Decimal | str | float = Decimal("0.00"),
        start_date: date | None = None,
        first_due_date: date | None = None,
        amortization_method: AmortizationMethod | str = AmortizationMethod.SIMPLE,
        notes: str = "",
    ) -> Debt:
        now = _utcnow()
        debt = cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            creditor_name=creditor_name,
            principal_amount=principal_amount,
            interest_rate=interest_rate,
            interest_rate_type=InterestRateType.safe(interest_rate_type),
            payment_frequency=PaymentFrequency.safe(payment_frequency),
            installment_count=installment_count,
            installment_amount=installment_amount,
            start_date=start_date or today(),
            first_due_date=first_due_date or today(),
            amortization_method=AmortizationMethod.safe(amortization_method),
            status=LoanStatus.ACTIVE,
            notes=notes or "",
            created_at=now,
            updated_at=now,
        )
        # installment_amount enviado se ignora: manda la cuota calculada.
        return debt._with(installment_amount=debt.generate_schedule()[0].total_due)

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        creditor_name: object,
        principal_amount: object,
        interest_rate: object = Decimal("0.00"),
        interest_rate_type: object = InterestRateType.PERCENTAGE,
        payment_frequency: object = PaymentFrequency.MONTHLY,
        installment_count: object = 1,
        installment_amount: object = Decimal("0.00"),
        start_date: object = None,
        first_due_date: object = None,
        amortization_method: object = AmortizationMethod.SIMPLE,
        status: object = LoanStatus.ACTIVE,
        notes: object = "",
        created_at: object = None,
        updated_at: object = None,
    ) -> Debt:
        # Sin monto mágico: None/0 falla en __post_init__ con DEBT_PRINCIPAL_NOT_POSITIVE.
        amount = (
            Money.from_value(principal_amount).amount
            if principal_amount is not None
            else Decimal("0.00")
        )
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            creditor_name=clean_str(creditor_name, ""),
            principal_amount=amount,
            interest_rate=interest_rate,
            interest_rate_type=InterestRateType.safe(interest_rate_type),
            payment_frequency=PaymentFrequency.safe(payment_frequency),
            installment_count=int(installment_count or 1),
            installment_amount=Money.from_value(installment_amount).amount,
            start_date=safe_date(start_date),
            first_due_date=safe_date(first_due_date),
            amortization_method=AmortizationMethod.safe(amortization_method),
            status=LoanStatus.safe(status),
            notes=clean_str(notes, ""),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_cancelled(self) -> bool:
        return self.status == LoanStatus.CANCELLED

    def is_paid(self) -> bool:
        return self.status == LoanStatus.PAID

    def mark_paid(self) -> Debt:
        """Cierre: todas las cuotas pagadas. Solo desde register_payment."""
        if self.is_cancelled():
            raise ValidationError(
                code="DEBT_CANCELLED",
                message="Deuda cancelada no puede marcarse pagada.",
            )
        if self.is_paid():
            return self
        return self._with(status=LoanStatus.PAID)

    def total_interest(self) -> Decimal:
        return _total_interest(
            self.principal_amount, self.interest_rate, self.interest_rate_type
        )

    def generate_schedule(self) -> list[DebtInstallment]:
        """Cronograma de cuotas (contado = 1 cuota). Puro: sin persistencia."""
        now = _utcnow()
        return [
            DebtInstallment(
                id=str(uuid.uuid4()),
                debt_id=self.id,
                installment_number=s.number,
                due_date=s.due_date,
                principal_due=s.principal_due,
                interest_due=s.interest_due,
                total_due=s.total_due,
                created_at=now,
            )
            for s in build_schedule(
                principal=self.principal_amount,
                interest_rate=self.interest_rate,
                interest_rate_type=self.interest_rate_type,
                installment_count=self.installment_count,
                frequency=self.payment_frequency,
                first_due_date=self.first_due_date,
            )
        ]

    def update_details(
        self, *, creditor_name: str | None = None, notes: str | None = None
    ) -> Debt:
        """Solo metadatos: el principal/condiciones no se editan (sin recalcular)."""
        self._ensure_mutable("editarse")
        return self._with(
            creditor_name=_validate_name(creditor_name)
            if creditor_name is not None
            else self.creditor_name,
            notes=_validate_notes(notes) if notes is not None else self.notes,
        )

    def cancel(self) -> Debt:
        """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""
        if self.status == LoanStatus.PAID:
            raise BusinessRuleError(
                code="DEBT_ALREADY_PAID",
                message="Deuda pagada no puede cancelarse.",
            )
        if self.is_cancelled():
            return self
        return self._with(status=LoanStatus.CANCELLED)

    def _ensure_mutable(self, action_description: str) -> None:
        if self.is_cancelled():
            raise ValidationError(
                code="DEBT_CANCELLED",
                message=f"Deuda cancelada no puede {action_description}.",
            )
        if self.status == LoanStatus.PAID:
            raise ValidationError(
                code="DEBT_ALREADY_PAID",
                message=f"Deuda pagada no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> Debt:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "creditor_name": self.creditor_name,
            "principal_amount": self.principal_amount,
            "interest_rate": self.interest_rate,
            "interest_rate_type": self.interest_rate_type,
            "payment_frequency": self.payment_frequency,
            "installment_count": self.installment_count,
            "installment_amount": self.installment_amount,
            "start_date": self.start_date,
            "first_due_date": self.first_due_date,
            "amortization_method": self.amortization_method,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Debt(**data)  # type: ignore[arg-type]
