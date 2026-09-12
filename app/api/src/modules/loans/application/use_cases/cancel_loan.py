from __future__ import annotations

from dataclasses import dataclass

from modules.loans.application.dtos import CancelLoanOutput, to_loan_output
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class CancelLoanInput:
    loan_id: str
    requester_id: str


class CancelLoanUseCase:
    """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""

    def __init__(self, repo: LoanRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CancelLoanInput) -> CancelLoanOutput:
        loan = await self._repo.find_by_id(inp.loan_id, for_update=True)

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

        cancelled = loan.cancel()
        await self._repo.save(cancelled)

        return to_loan_output(cancelled)
