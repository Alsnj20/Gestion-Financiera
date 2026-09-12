from __future__ import annotations

from dataclasses import dataclass

from modules.debts.application.dtos import GetDebtOutput, to_debt_output
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetDebtInput:
    debt_id: str
    requester_id: str
    requester_role: str = "USER"


class GetDebtUseCase:
    def __init__(self, repo: DebtRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetDebtInput) -> GetDebtOutput:
        debt = await self._repo.find_by_id(inp.debt_id)

        if debt is None:
            raise NotFoundError(
                code="DEBT_NOT_FOUND",
                message="Deuda no encontrada",
            )

        # Lectura: dueño o admin.
        if debt.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        installments = await self._repo.list_installments(debt.id)
        payments = await self._repo.list_payments(debt.id)
        return to_debt_output(debt, installments, payments)
