from __future__ import annotations

from dataclasses import dataclass

from modules.loans.application.dtos import ListLoansOutput, to_loan_output
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListLoansInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListLoansUseCase:
    def __init__(self, repo: LoanRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListLoansInput) -> list[ListLoansOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        loans = await self._repo.find_by_user(inp.user_id)
        return [
            to_loan_output(
                loan,
                await self._repo.list_installments(loan.id),
                await self._repo.list_payments(loan.id),
            )
            for loan in loans
        ]
