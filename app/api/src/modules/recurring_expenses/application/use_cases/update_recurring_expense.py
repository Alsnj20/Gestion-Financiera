from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.recurring_expenses.application.dtos import (
    UpdateRecurringExpenseOutput,
    to_recurring_expense_output,
)
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from modules.recurring_expenses.application.use_cases.create_recurring_expense import (
    _resolve_category,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateRecurringExpenseInput:
    re_id: str
    user_id: str
    amount: Decimal | None = None
    frequency: str | None = None
    next_date: date | None = None
    description: str | None = None
    category_id: str | None = None


class UpdateRecurringExpenseUseCase:
    def __init__(
        self,
        repo: RecurringExpenseRepositoryPort,
        category_repo: CategoryRepositoryPort,
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo

    async def execute(
        self, inp: UpdateRecurringExpenseInput
    ) -> UpdateRecurringExpenseOutput:
        item = await self._repo.find_by_id(inp.re_id)

        if item is None:
            raise NotFoundError(
                code="RE_NOT_FOUND",
                message="Gasto recurrente no encontrado",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if item.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        category_id = item.category_id
        if inp.category_id is not None and inp.category_id != item.category_id:
            category_id = await _resolve_category(
                self._category_repo, inp.user_id, inp.category_id
            )

        updated = item.update_details(
            amount=inp.amount,
            frequency=inp.frequency,
            next_date=inp.next_date,
            description=inp.description,
            category_id=category_id,
        )
        await self._repo.save(updated)

        return to_recurring_expense_output(updated)
