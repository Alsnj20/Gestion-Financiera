from __future__ import annotations

from dataclasses import dataclass

from modules.loans.application.dtos import UpdateLoanOutput, to_loan_output
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateLoanInput:
    loan_id: str
    requester_id: str
    borrower_name: str | None = None
    notes: str | None = None


class UpdateLoanUseCase:
    """Solo metadatos (borrower_name/notes).

    El principal y las condiciones no se editan: sin recalcular el
    cronograma, cambiarlos corrompe el agregado.
    """

    def __init__(self, repo: LoanRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: UpdateLoanInput) -> UpdateLoanOutput:
        loan = await self._repo.find_by_id(inp.loan_id)

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

        updated = loan.update_details(
            borrower_name=inp.borrower_name,
            notes=inp.notes,
        )
        await self._repo.save(updated)

        return to_loan_output(updated)
