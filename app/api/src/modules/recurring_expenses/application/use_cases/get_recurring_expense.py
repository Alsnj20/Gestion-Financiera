from __future__ import annotations

from dataclasses import dataclass

from modules.recurring_expenses.application.dtos import (
    GetRecurringExpenseOutput,
    to_recurring_expense_output,
)
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetRecurringExpenseInput:
    re_id: str
    requester_id: str
    requester_role: str = "USER"


class GetRecurringExpenseUseCase:
    def __init__(self, repo: RecurringExpenseRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetRecurringExpenseInput) -> GetRecurringExpenseOutput:
        item = await self._repo.find_by_id(inp.re_id)

        if item is None:
            raise NotFoundError(
                code="RE_NOT_FOUND",
                message="Gasto recurrente no encontrado",
            )

        # Lectura: dueño o admin.
        if item.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_recurring_expense_output(item)
