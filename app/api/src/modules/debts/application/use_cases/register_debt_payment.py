from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from modules.debts.domain.entities.debt import DebtPayment
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transactions.domain.entities.transaction import Transaction
from shared.domain.guards import today
from shared.errors import BusinessRuleError, NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class RegisterDebtPaymentInput:
    debt_id: str
    requester_id: str
    account_id: str
    installment_id: str
    principal_amount: Decimal
    interest_amount: Decimal = Decimal("0.00")
    payment_date: date | None = None
    category_id: str = ""
    payment_method_id: str = ""
    description: str = ""


@dataclass(frozen=True, slots=True)
class RegisterDebtPaymentOutput:
    payment_id: str
    debt_id: str
    installment_id: str
    transaction_id: str
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    installment_status: str
    debt_status: str


class RegisterDebtPaymentUseCase:
    """Registra un pago de deuda: Transaction EXPENSE + Payment + cuota + balance.

    Deber no mueve dinero solo; pagar sí: el egreso sale de la cuenta.
    Todo en una única unidad de trabajo.
    """

    def __init__(
        self,
        debt_repo: DebtRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        account_repo: AccountRepositoryPort,
    ) -> None:
        self._debt_repo = debt_repo
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: RegisterDebtPaymentInput) -> RegisterDebtPaymentOutput:
        debt = await self._debt_repo.find_by_id(inp.debt_id, for_update=True)

        if debt is None:
            raise NotFoundError(
                code="DEBT_NOT_FOUND",
                message="Deuda no encontrada",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if debt.user_id != inp.requester_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        if debt.is_cancelled():
            raise ValidationError(
                code="DEBT_CANCELLED",
                message="Deuda cancelada no puede registrar pagos.",
            )
        if debt.is_paid():
            raise BusinessRuleError(
                code="DEBT_ALREADY_PAID",
                message="Deuda ya pagada.",
            )

        installments = await self._debt_repo.list_installments(debt.id)
        installment = next(
            (i for i in installments if i.id == inp.installment_id), None
        )
        if installment is None:
            raise NotFoundError(
                code="DEBT_INSTALLMENT_NOT_FOUND",
                message="Cuota no encontrada",
            )

        principal = inp.principal_amount
        interest = inp.interest_amount
        if principal < Decimal("0.00") or interest < Decimal("0.00"):
            raise ValidationError(
                code="DEBT_PAYMENT_NEGATIVE",
                message="El pago no puede ser negativo.",
            )
        total = principal + interest
        if total <= Decimal("0.00"):
            raise ValidationError(
                code="DEBT_PAYMENT_NOT_POSITIVE",
                message="El pago debe ser mayor a cero.",
            )
        pending = (installment.principal_due - installment.principal_paid) + (
            installment.interest_due - installment.interest_paid
        )
        if total > pending:
            raise ValidationError(
                code="DEBT_PAYMENT_EXCEEDS",
                message=f"El pago ({total}) excede el pendiente ({pending}).",
            )

        account = await self._account_repo.find_by_id(inp.account_id, for_update=True)
        if account is None:
            raise ValidationError(
                code="ACCOUNT_NOT_FOUND", message="Cuenta no encontrada"
            )
        if account.user_id != inp.requester_id:
            raise BusinessRuleError(
                code="FORBIDDEN", message="La cuenta no pertenece al usuario"
            )

        payment_date = inp.payment_date or today()
        tx_datetime = datetime(
            payment_date.year, payment_date.month, payment_date.day, tzinfo=UTC
        )
        description = inp.description or f"Pago deuda {debt.creditor_name}"

        tx = Transaction.create_expense(
            user_id=inp.requester_id,
            account_id=account.id,
            amount=total,
            currency=account.currency,
            description=description,
            category_id=inp.category_id,
            payment_method_id=inp.payment_method_id,
            transaction_date=tx_datetime,
        )
        updated_account = account.apply_expense(total)
        updated_installment = installment.apply_payment(principal, interest)
        payment = DebtPayment(
            id=str(uuid.uuid4()),
            debt_id=debt.id,
            transaction_id=tx.id,
            payment_date=payment_date,
            principal_amount=principal,
            interest_amount=interest,
            total_amount=total,
            installment_id=installment.id,
        )

        await self._tx_repo.save(tx)
        await self._account_repo.save(updated_account)
        await self._debt_repo.save_installment(updated_installment)
        await self._debt_repo.save_payment(payment)

        others_paid = all(
            i.is_paid for i in installments if i.id != updated_installment.id
        )
        if others_paid and updated_installment.is_paid:
            debt = debt.mark_paid()
            await self._debt_repo.save(debt)

        return RegisterDebtPaymentOutput(
            payment_id=payment.id,
            debt_id=debt.id,
            installment_id=updated_installment.id,
            transaction_id=tx.id,
            principal_amount=principal,
            interest_amount=interest,
            total_amount=total,
            installment_status=updated_installment.status.value,
            debt_status=debt.status.value,
        )
