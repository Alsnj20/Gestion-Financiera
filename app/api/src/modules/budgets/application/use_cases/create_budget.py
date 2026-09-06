from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from modules.budgets.domain.entities.budget import Budget
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort


@dataclass(frozen=True, slots=True)
class CreateBudgetInput:
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str = ""


@dataclass(frozen=True, slots=True)
class CreateBudgetOutput:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str
    status: str


class CreateBudgetUseCase:
    def __init__(self, repo: BudgetRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateBudgetInput) -> CreateBudgetOutput:
        budget = Budget.create(
            user_id=inp.user_id, name=inp.name, amount=inp.amount,
            period_start=inp.period_start, period_end=inp.period_end, category_id=inp.category_id,
        )
        await self._repo.save(budget)

        return CreateBudgetOutput(
            id=budget.id, user_id=budget.user_id, name=budget.name, amount=budget.amount,
            period_start=budget.period_start, period_end=budget.period_end, category_id=budget.category_id,
            status=budget.status.value if hasattr(budget.status, "value") else str(budget.status),
        )
