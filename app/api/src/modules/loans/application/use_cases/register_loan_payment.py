from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from modules.loans.domain.entities.loan import LoanPayment
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transactions.domain.entities.transaction import Transaction
from shared.domain.guards import today
from shared.errors import BusinessRuleError, NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class RegisterLoanPaymentInput:
    loan_id: str
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
class RegisterLoanPaymentOutput:
    payment_id: str
    loan_id: str
    installment_id: str
    transaction_id: str
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    installment_status: str
    loan_status: str


class RegisterLoanPaymentUseCase:
    """Registra un cobro: Transaction INCOME + Payment + cuota + balance.

    Prestar no mueve dinero solo; cobrar sí: el ingreso entra a la cuenta.
    Todo en una única unidad de trabajo.
    """

    def __init__(
        self,
        loan_repo: LoanRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        account_repo: AccountRepositoryPort,
    ) -> None:
        self._loan_repo = loan_repo
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: RegisterLoanPaymentInput) -> RegisterLoanPaymentOutput:
        loan = await self._loan_repo.find_by_id(inp.loan_id, for_update=True)

        if loan is None:
            raise NotFoundError(
                code="LOAN_NOT_FOUND",
                message="Préstamo no encontrado",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if loan.user_id != inp.requester_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        if loan.is_cancelled():
            raise ValidationError(
                code="LOAN_CANCELLED",
                message="Préstamo cancelado no puede registrar pagos.",
            )
        if loan.is_paid():
            raise BusinessRuleError(
                code="LOAN_ALREADY_PAID",
                message="Préstamo ya pagado.",
            )

        installments = await self._loan_repo.list_installments(loan.id)
        installment = next(
            (i for i in installments if i.id == inp.installment_id), None
        )
        if installment is None:
            raise NotFoundError(
                code="LOAN_INSTALLMENT_NOT_FOUND",
                message="Cuota no encontrada",
            )

        principal = inp.principal_amount
        interest = inp.interest_amount
        if principal < Decimal("0.00") or interest < Decimal("0.00"):
            raise ValidationError(
                code="LOAN_PAYMENT_NEGATIVE",
                message="El pago no puede ser negativo.",
            )
        total = principal + interest
        if total <= Decimal("0.00"):
            raise ValidationError(
                code="LOAN_PAYMENT_NOT_POSITIVE",
                message="El pago debe ser mayor a cero.",
            )
        pending = (installment.principal_due - installment.principal_paid) + (
            installment.interest_due - installment.interest_paid
        )
        if total > pending:
            raise ValidationError(
                code="LOAN_PAYMENT_EXCEEDS",
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
        description = inp.description or f"Cobro préstamo {loan.borrower_name}"

        tx = Transaction.create_income(
            user_id=inp.requester_id,
            account_id=account.id,
            amount=total,
            currency=account.currency,
            concepto=description,
            category_id=inp.category_id,
            payment_method_id=inp.payment_method_id,
            transaction_date=tx_datetime,
        )
        updated_account = account.apply_income(total)
        updated_installment = installment.apply_payment(principal, interest)
        payment = LoanPayment(
            id=str(uuid.uuid4()),
            loan_id=loan.id,
            transaction_id=tx.id,
            payment_date=payment_date,
            principal_amount=principal,
            interest_amount=interest,
            total_amount=total,
            installment_id=installment.id,
        )

        await self._tx_repo.save(tx)
        await self._account_repo.save(updated_account)
        await self._loan_repo.save_installment(updated_installment)
        await self._loan_repo.save_payment(payment)

        others_paid = all(
            i.is_paid for i in installments if i.id != updated_installment.id
        )
        if others_paid and updated_installment.is_paid:
            loan = loan.mark_paid()
            await self._loan_repo.save(loan)

        return RegisterLoanPaymentOutput(
            payment_id=payment.id,
            loan_id=loan.id,
            installment_id=updated_installment.id,
            transaction_id=tx.id,
            principal_amount=principal,
            interest_amount=interest,
            total_amount=total,
            installment_status=updated_installment.status.value,
            loan_status=loan.status.value,
        )
