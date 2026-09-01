from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from shared.domain.value_objects.money import Money
from shared.errors import ValidationError
from shared.types.enums import AmortizationMethod, InterestRateType, LoanStatus, PaymentFrequency

MAX_NAME_LEN = 120
MAX_NOTES_LEN = 1000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _safe_date(v: object, default: date | None = None) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip())
        except ValueError:
            return default or date.today()
    return default or date.today()


@dataclass(slots=True)
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
    status: str = "PENDING"
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        from shared.types.enums import InstallmentStatus

        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.debt_id = _safe_str(self.debt_id)
        self.status = InstallmentStatus.safe(self.status).value
        self.installment_number = int(self.installment_number) if self.installment_number is not None else 1
        if self.installment_number < 1:
            self.installment_number = 1
        self.due_date = _safe_date(self.due_date)
        self.principal_due = Money.from_value(self.principal_due).amount
        self.interest_due = Money.from_value(self.interest_due).amount
        self.total_due = Money.from_value(self.total_due).amount if self.total_due is not None else self.principal_due + self.interest_due
        self.principal_paid = Money.from_value(self.principal_paid).amount
        self.interest_paid = Money.from_value(self.interest_paid).amount


@dataclass(slots=True)
class DebtPayment:
    id: str
    debt_id: str
    transaction_id: str
    payment_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    installment_id: str = ""
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.debt_id = _safe_str(self.debt_id)
        self.transaction_id = _safe_str(self.transaction_id)
        self.installment_id = _safe_str(self.installment_id, "")
        self.payment_date = _safe_date(self.payment_date)
        self.principal_amount = Money.from_value(self.principal_amount).amount
        self.interest_amount = Money.from_value(self.interest_amount).amount
        self.total_amount = Money.from_value(self.total_amount).amount if self.total_amount is not None else self.principal_amount + self.interest_amount


@dataclass(slots=True)
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
    start_date: date = field(default_factory=date.today)
    first_due_date: date = field(default_factory=date.today)
    amortization_method: AmortizationMethod = AmortizationMethod.SIMPLE
    status: LoanStatus = LoanStatus.ACTIVE
    notes: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.creditor_name = _safe_str(self.creditor_name)
        self.notes = _safe_str(self.notes, "")[:MAX_NOTES_LEN]
        self.interest_rate_type = InterestRateType.safe(self.interest_rate_type)
        self.payment_frequency = PaymentFrequency.safe(self.payment_frequency)
        self.amortization_method = AmortizationMethod.safe(self.amortization_method)
        self.status = LoanStatus.safe(self.status)
        self.principal_amount = Money.from_value(self.principal_amount).amount
        self.interest_rate = Money.from_value(self.interest_rate).amount
        self.installment_amount = Money.from_value(self.installment_amount).amount
        self.installment_count = int(self.installment_count) if self.installment_count is not None else 1
        if self.installment_count < 1:
            self.installment_count = 1
        self.start_date = _safe_date(self.start_date)
        self.first_due_date = _safe_date(self.first_due_date)

        if not self.user_id:
            raise ValidationError(code="DEBT_USER_REQUIRED", message="user_id requerido")
        if not self.creditor_name:
            raise ValidationError(code="DEBT_CREDITOR_REQUIRED", message="creditor_name requerido")
        if len(self.creditor_name) > MAX_NAME_LEN:
            raise ValidationError(code="DEBT_CREDITOR_TOO_LONG", message=f"creditor_name excede {MAX_NAME_LEN}")
        if self.principal_amount <= Decimal("0.00"):
            raise ValidationError(code="DEBT_PRINCIPAL_NOT_POSITIVE", message="principal_amount debe ser > 0")

    @classmethod
    def create(cls, *, user_id: str, creditor_name: str, principal_amount: Decimal | str | float | int, interest_rate: Decimal | str | float | int = Decimal("0.00"), interest_rate_type: InterestRateType | str = InterestRateType.PERCENTAGE, payment_frequency: PaymentFrequency | str = PaymentFrequency.MONTHLY, installment_count: int = 1, installment_amount: Decimal | str | float | int = Decimal("0.00"), start_date: date | None = None, first_due_date: date | None = None, amortization_method: AmortizationMethod | str = AmortizationMethod.SIMPLE, notes: str = "") -> Debt:
        now = _utcnow()
        return cls(id=str(uuid.uuid4()), user_id=user_id, creditor_name=creditor_name, principal_amount=Money.from_value(principal_amount).amount, interest_rate=Money.from_value(interest_rate).amount, interest_rate_type=InterestRateType.safe(interest_rate_type), payment_frequency=PaymentFrequency.safe(payment_frequency), installment_count=installment_count, installment_amount=Money.from_value(installment_amount).amount, start_date=start_date or date.today(), first_due_date=first_due_date or date.today(), amortization_method=AmortizationMethod.safe(amortization_method), status=LoanStatus.ACTIVE, notes=notes or "", created_at=now, updated_at=now)

    @classmethod
    def rehydrate(cls, **kwargs: object) -> Debt:  # type: ignore[no-untyped-def]
        return cls(
            id=_safe_str(kwargs.get("id")) or str(uuid.uuid4()),
            user_id=_safe_str(kwargs.get("user_id"), ""),
            creditor_name=_safe_str(kwargs.get("creditor_name"), "Unknown"),
            principal_amount=Money.from_value(kwargs.get("principal_amount")).amount if kwargs.get("principal_amount") is not None else Decimal("0.01"),
            interest_rate=Money.from_value(kwargs.get("interest_rate", Decimal("0.00"))).amount,
            interest_rate_type=InterestRateType.safe(kwargs.get("interest_rate_type")),
            payment_frequency=PaymentFrequency.safe(kwargs.get("payment_frequency")),
            installment_count=int(kwargs.get("installment_count") or 1),  # type: ignore[arg-type]
            installment_amount=Money.from_value(kwargs.get("installment_amount", Decimal("0.00"))).amount,
            start_date=_safe_date(kwargs.get("start_date")),
            first_due_date=_safe_date(kwargs.get("first_due_date")),
            amortization_method=AmortizationMethod.safe(kwargs.get("amortization_method")),
            status=LoanStatus.safe(kwargs.get("status")),
            notes=_safe_str(kwargs.get("notes"), "")[:MAX_NOTES_LEN],
            created_at=kwargs.get("created_at") if isinstance(kwargs.get("created_at"), datetime) else _utcnow(),
            updated_at=kwargs.get("updated_at") if isinstance(kwargs.get("updated_at"), datetime) else _utcnow(),
        )
