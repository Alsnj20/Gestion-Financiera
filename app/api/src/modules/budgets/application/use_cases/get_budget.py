from __future__ import annotations

from dataclasses import dataclass

from modules.budgets.application.dtos import GetBudgetOutput, to_budget_output
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetBudgetInput:
    budget_id: str
    requester_id: str
    requester_role: str = "USER"


class GetBudgetUseCase:
    def __init__(self, repo: BudgetRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetBudgetInput) -> GetBudgetOutput:
        budget = await self._repo.find_by_id(inp.budget_id)

        if budget is None:
            raise NotFoundError(
                code="BUDGET_NOT_FOUND",
                message="Presupuesto no encontrado",
            )

        # Lectura: dueño o admin.
        if budget.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_budget_output(budget)
