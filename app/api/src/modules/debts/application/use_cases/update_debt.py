from __future__ import annotations

from dataclasses import dataclass

from modules.debts.application.dtos import UpdateDebtOutput, to_debt_output
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateDebtInput:
    debt_id: str
    requester_id: str
    creditor_name: str | None = None
    notes: str | None = None


class UpdateDebtUseCase:
    """Solo metadatos (creditor_name/notes).

    El principal y las condiciones no se editan: sin recalcular el
    cronograma, cambiarlos corrompe el agregado.
    """

    def __init__(self, repo: DebtRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: UpdateDebtInput) -> UpdateDebtOutput:
        debt = await self._repo.find_by_id(inp.debt_id)

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

        updated = debt.update_details(
            creditor_name=inp.creditor_name,
            notes=inp.notes,
        )
        await self._repo.save(updated)

        return to_debt_output(updated)
