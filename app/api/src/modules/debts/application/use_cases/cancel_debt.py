from __future__ import annotations

from dataclasses import dataclass

from modules.debts.application.dtos import CancelDebtOutput, to_debt_output
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class CancelDebtInput:
    debt_id: str
    requester_id: str


class CancelDebtUseCase:
    """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""

    def __init__(self, repo: DebtRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CancelDebtInput) -> CancelDebtOutput:
        debt = await self._repo.find_by_id(inp.debt_id, for_update=True)

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

        cancelled = debt.cancel()
        await self._repo.save(cancelled)

        return to_debt_output(cancelled)
