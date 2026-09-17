from __future__ import annotations

from dataclasses import dataclass

from modules.recurring_expenses.application.dtos import (
    RecurringExpenseOutput as CancelRecurringExpenseOutput,
)
from modules.recurring_expenses.application.dtos import (
    to_recurring_expense_output,
)
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class CancelRecurringExpenseInput:
    re_id: str
    user_id: str


class CancelRecurringExpenseUseCase:
    """Anulación lógica: la fila se conserva con CANCELLED, nunca se borra."""

    def __init__(self, repo: RecurringExpenseRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: CancelRecurringExpenseInput
    ) -> CancelRecurringExpenseOutput:
        item = await self._repo.find_by_id(inp.re_id, for_update=True)

        if item is None:
            raise NotFoundError(
                code="RE_NOT_FOUND",
                message="Gasto recurrente no encontrado",
            )

        if item.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        cancelled = item.cancel()
        await self._repo.save(cancelled)

        return to_recurring_expense_output(cancelled)
