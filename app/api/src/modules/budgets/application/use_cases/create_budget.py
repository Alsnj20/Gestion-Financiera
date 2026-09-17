from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.budgets.application.dtos import CreateBudgetOutput, to_budget_output
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from modules.budgets.domain.entities.budget import Budget
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class CreateBudgetInput:
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str = ""


async def _resolve_category(
    category_repo: CategoryRepositoryPort, user_id: str, category_id: str
) -> str:
    """La categoría debe existir y ser del usuario (presupuesto con causa)."""
    if not category_id:
        return ""
    category = await category_repo.find_by_id(category_id)
    if category is None:
        raise NotFoundError(
            code="BUDGET_CATEGORY_NOT_FOUND",
            message="Categoría no encontrada",
        )
    if category.user_id != user_id:
        raise BusinessRuleError(
            code="FORBIDDEN",
            message="No autorizado",
        )
    if category.is_archived():
        raise BusinessRuleError(
            code="BUDGET_CATEGORY_ARCHIVED",
            message="La categoría está archivada.",
        )
    return category.id


class CreateBudgetUseCase:
    def __init__(
        self, repo: BudgetRepositoryPort, category_repo: CategoryRepositoryPort
    ) -> None:
        self._repo = repo
        self._category_repo = category_repo

    async def execute(self, inp: CreateBudgetInput) -> CreateBudgetOutput:
        category_id = await _resolve_category(
            self._category_repo, inp.user_id, inp.category_id
        )

        budget = Budget.create(
            user_id=inp.user_id,
            name=inp.name,
            amount=inp.amount,
            period_start=inp.period_start,
            period_end=inp.period_end,
            category_id=category_id,
        )
        await self._repo.save(budget)

        return to_budget_output(budget)
