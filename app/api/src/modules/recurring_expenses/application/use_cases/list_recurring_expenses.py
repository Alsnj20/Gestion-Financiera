from __future__ import annotations

from dataclasses import dataclass

from modules.recurring_expenses.application.dtos import (
    ListRecurringExpensesOutput,
    to_recurring_expense_output,
)
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListRecurringExpensesInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListRecurringExpensesUseCase:
    def __init__(self, repo: RecurringExpenseRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: ListRecurringExpensesInput
    ) -> list[ListRecurringExpensesOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        items = await self._repo.find_by_user(inp.user_id)
        return [to_recurring_expense_output(item) for item in items]
