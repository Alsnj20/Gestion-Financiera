from __future__ import annotations

from typing import Protocol
from modules.recurring_expenses.domain.entities.recurring_expense import RecurringExpense


class RecurringExpenseRepositoryPort(Protocol):
    async def save(self, recurring_expense: RecurringExpense) -> None: ...
    async def find_by_id(self, recurring_expense_id: str) -> RecurringExpense | None: ...
    async def find_by_user(self, user_id: str) -> list[RecurringExpense]: ...
