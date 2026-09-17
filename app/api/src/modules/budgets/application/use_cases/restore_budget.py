from __future__ import annotations

from dataclasses import dataclass

from modules.budgets.application.dtos import RestoreBudgetOutput, to_budget_output
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class RestoreBudgetInput:
    budget_id: str
    user_id: str


class RestoreBudgetUseCase:
    def __init__(self, repo: BudgetRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: RestoreBudgetInput) -> RestoreBudgetOutput:
        budget = await self._repo.find_by_id(inp.budget_id, for_update=True)

        if budget is None:
            raise NotFoundError(
                code="BUDGET_NOT_FOUND",
                message="Presupuesto no encontrado",
            )

        # Solo el dueño restaura.
        if budget.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        restored = budget.restore()
        await self._repo.save(restored)

        return to_budget_output(restored)
