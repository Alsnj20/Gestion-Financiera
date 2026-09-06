from __future__ import annotations

from dataclasses import dataclass
from modules.recurring_expenses.domain.entities.recurring_expense import RecurringExpense
from modules.recurring_expenses.application.ports.recurring_expense_repository import RecurringExpenseRepositoryPort


@dataclass(frozen=True, slots=True)
class ListRecurringExpensesInput:
    user_id: str


@dataclass(frozen=True, slots=True)
class ListRecurringExpensesOutput:
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: str
    frequency: str
    next_date: str
    description: str
    status: str


class ListRecurringExpensesUseCase:
    def __init__(self, repo: RecurringExpenseRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListRecurringExpensesInput) -> list[ListRecurringExpensesOutput]:
        items = await self._repo.find_by_user(inp.user_id)
        return [
            ListRecurringExpensesOutput(
                id=r.id,
                user_id=r.user_id,
                account_id=r.account_id,
                category_id=r.category_id,
                amount=str(r.amount),
                frequency=r.frequency.value if hasattr(r.frequency, "value") else str(r.frequency),
                next_date=str(r.next_date),
                description=r.description,
                status=r.status,
            )
            for r in items
        ]
