from __future__ import annotations

from dataclasses import dataclass

from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class ArchiveBudgetInput:
    budget_id: str
    user_id: str


class ArchiveBudgetUseCase:
    def __init__(self, repo: BudgetRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ArchiveBudgetInput) -> None:
        budget = await self._repo.find_by_id(inp.budget_id, for_update=True)

        if budget is None:
            raise NotFoundError(
                code="BUDGET_NOT_FOUND",
                message="Presupuesto no encontrado",
            )

        # Only the owner can archive the budget.
        if budget.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        # If the budget is already archived, we don't need to do anything.
        if budget.is_archived():
            return

        await self._repo.save(budget.archive())
