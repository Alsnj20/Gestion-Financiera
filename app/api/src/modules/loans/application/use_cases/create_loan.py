from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.loans.application.dtos import CreateLoanOutput, to_loan_output
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from modules.loans.domain.entities.loan import Loan


@dataclass(frozen=True, slots=True)
class CreateLoanInput:
    user_id: str
    borrower_name: str
    principal_amount: Decimal
    interest_rate: Decimal = Decimal("0.00")
    interest_rate_type: str = "PERCENTAGE"
    payment_frequency: str = "MONTHLY"
    installment_count: int = 1
    installment_amount: Decimal = Decimal("0.00")
    start_date: date | None = None
    first_due_date: date | None = None
    amortization_method: str = "SIMPLE"
    notes: str = ""


class CreateLoanUseCase:
    def __init__(self, repo: LoanRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateLoanInput) -> CreateLoanOutput:
        loan = Loan.create(
            user_id=inp.user_id,
            borrower_name=inp.borrower_name,
            principal_amount=inp.principal_amount,
            interest_rate=inp.interest_rate,
            interest_rate_type=inp.interest_rate_type,
            payment_frequency=inp.payment_frequency,
            installment_count=inp.installment_count,
            installment_amount=inp.installment_amount,
            start_date=inp.start_date,
            first_due_date=inp.first_due_date,
            amortization_method=inp.amortization_method,
            notes=inp.notes,
        )
        # Cronograma al crear (contado = 1 cuota); misma unidad de trabajo.
        schedule = loan.generate_schedule()
        await self._repo.save(loan)
        await self._repo.save_installments(schedule)

        return to_loan_output(loan, schedule)
