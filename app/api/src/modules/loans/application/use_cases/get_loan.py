from __future__ import annotations

from dataclasses import dataclass

from modules.loans.application.dtos import GetLoanOutput, to_loan_output
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetLoanInput:
    loan_id: str
    requester_id: str
    requester_role: str = "USER"


class GetLoanUseCase:
    def __init__(self, repo: LoanRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetLoanInput) -> GetLoanOutput:
        loan = await self._repo.find_by_id(inp.loan_id)

        if loan is None:
            raise NotFoundError(
                code="LOAN_NOT_FOUND",
                message="Préstamo no encontrado",
            )

        # Lectura: dueño o admin.
        if loan.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        installments = await self._repo.list_installments(loan.id)
        payments = await self._repo.list_payments(loan.id)
        return to_loan_output(loan, installments, payments)
