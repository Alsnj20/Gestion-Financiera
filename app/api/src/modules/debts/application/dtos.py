"""DTOs de salida unificados del módulo debts.

Fuente única: `DebtOutput` + `to_debt_output` (con cronograma).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.debts.domain.entities.debt import Debt, DebtInstallment, DebtPayment


@dataclass(frozen=True, slots=True)
class InstallmentOutput:
    id: str
    number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    status: str


def to_installment_output(inst: DebtInstallment) -> InstallmentOutput:
    return InstallmentOutput(
        id=inst.id,
        number=inst.installment_number,
        due_date=inst.due_date,
        principal_due=inst.principal_due,
        interest_due=inst.interest_due,
        total_due=inst.total_due,
        principal_paid=inst.principal_paid,
        interest_paid=inst.interest_paid,
        status=inst.status.value,
    )


@dataclass(frozen=True, slots=True)
class PaymentOutput:
    id: str
    installment_id: str
    transaction_id: str
    payment_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal


def to_payment_output(payment: DebtPayment) -> PaymentOutput:
    return PaymentOutput(
        id=payment.id,
        installment_id=payment.installment_id,
        transaction_id=payment.transaction_id,
        payment_date=payment.payment_date,
        principal_amount=payment.principal_amount,
        interest_amount=payment.interest_amount,
        total_amount=payment.total_amount,
    )


@dataclass(frozen=True, slots=True)
class DebtOutput:
    id: str
    user_id: str
    creditor_name: str
    principal_amount: Decimal
    status: str
    installments: tuple[InstallmentOutput, ...] = ()
    payments: tuple[PaymentOutput, ...] = ()


def to_debt_output(
    debt: Debt,
    installments: list[DebtInstallment] | None = None,
    payments: list[DebtPayment] | None = None,
) -> DebtOutput:
    return DebtOutput(
        id=debt.id,
        user_id=debt.user_id,
        creditor_name=debt.creditor_name,
        principal_amount=debt.principal_amount,
        status=debt.status.value,
        installments=tuple(to_installment_output(i) for i in (installments or [])),
        payments=tuple(to_payment_output(p) for p in (payments or [])),
    )


# Aliases de compatibilidad.
CreateDebtOutput = DebtOutput
GetDebtOutput = DebtOutput
ListDebtsOutput = DebtOutput
UpdateDebtOutput = DebtOutput
CancelDebtOutput = DebtOutput
