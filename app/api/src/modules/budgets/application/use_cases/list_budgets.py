from __future__ import annotations

from dataclasses import dataclass

from modules.budgets.application.dtos import ListBudgetsOutput, to_budget_output
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from shared.errors import BusinessRuleError
from shared.types.enums import BudgetStatus


@dataclass(frozen=True, slots=True)
class ListBudgetsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"
    include_archived: bool = False


class ListBudgetsUseCase:
    def __init__(self, repo: BudgetRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListBudgetsInput) -> list[ListBudgetsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        budgets = await self._repo.find_by_user(inp.user_id)
        if not inp.include_archived:
            budgets = [b for b in budgets if b.status == BudgetStatus.ACTIVE]
        return [to_budget_output(b) for b in budgets]
