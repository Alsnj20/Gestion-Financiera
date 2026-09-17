"""DTOs de salida unificados del módulo budgets.

Fuente única: `BudgetOutput` + `to_budget_output`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.budgets.domain.entities.budget import Budget


@dataclass(frozen=True, slots=True)
class BudgetOutput:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_start: date
    period_end: date
    category_id: str
    status: str


def to_budget_output(budget: Budget) -> BudgetOutput:
    return BudgetOutput(
        id=budget.id,
        user_id=budget.user_id,
        name=budget.name,
        amount=budget.amount,
        period_start=budget.period_start,
        period_end=budget.period_end,
        category_id=budget.category_id,
        status=budget.status.value,
    )


# Aliases de compatibilidad.
CreateBudgetOutput = BudgetOutput
GetBudgetOutput = BudgetOutput
ListBudgetsOutput = BudgetOutput
UpdateBudgetOutput = BudgetOutput
RestoreBudgetOutput = BudgetOutput
