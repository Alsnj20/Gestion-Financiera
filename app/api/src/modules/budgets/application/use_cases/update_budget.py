from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.budgets.application.dtos import UpdateBudgetOutput, to_budget_output
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from modules.budgets.application.use_cases.create_budget import _resolve_category
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateBudgetInput:
    budget_id: str
    user_id: str
    name: str | None = None
    amount: Decimal | None = None
    period_start: date | None = None
    period_end: date | None = None
    category_id: str | None = None


class UpdateBudgetUseCase:
    def __init__(
        self, repo: BudgetRepositoryPort, category_repo: CategoryRepositoryPort
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo

    async def execute(self, inp: UpdateBudgetInput) -> UpdateBudgetOutput:
        budget = await self._repo.find_by_id(inp.budget_id)

        if budget is None:
            raise NotFoundError(
                code="BUDGET_NOT_FOUND",
                message="Presupuesto no encontrado",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if budget.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )
        if budget.is_archived():
            raise BusinessRuleError(
                code="BUDGET_ARCHIVED",
                message="Presupuesto archivado no se puede editar. Restaúralo primero.",
            )

        category_id = budget.category_id
        if inp.category_id is not None and inp.category_id != budget.category_id:
            category_id = await _resolve_category(
                self._category_repo, inp.user_id, inp.category_id
            )

        updated = budget.update_details(
            name=inp.name,
            amount=inp.amount,
            period_start=inp.period_start,
            period_end=inp.period_end,
            category_id=category_id,
        )
        await self._repo.save(updated)

        return to_budget_output(updated)
