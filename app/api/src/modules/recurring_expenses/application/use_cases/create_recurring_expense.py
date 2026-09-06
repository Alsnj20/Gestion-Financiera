from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from modules.recurring_expenses.domain.entities.recurring_expense import RecurringExpense
from modules.recurring_expenses.application.ports.recurring_expense_repository import RecurringExpenseRepositoryPort


@dataclass(frozen=True, slots=True)
class CreateRecurringExpenseInput:
    user_id: str
    account_id: str
    amount: float | str | int
    frequency: str = "MONTHLY"
    next_date: date | None = None
    description: str = ""
    category_id: str = ""


@dataclass(frozen=True, slots=True)
class CreateRecurringExpenseOutput:
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: str
    frequency: str
    next_date: str
    description: str
    status: str


class CreateRecurringExpenseUseCase:
    def __init__(self, repo: RecurringExpenseRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateRecurringExpenseInput) -> CreateRecurringExpenseOutput:
        re = RecurringExpense.create(
            user_id=inp.user_id,
            account_id=inp.account_id,
            amount=inp.amount,
            frequency=inp.frequency,
            next_date=inp.next_date or date.today(),
            description=inp.description,
            category_id=inp.category_id,
        )
        await self._repo.save(re)

        return CreateRecurringExpenseOutput(
            id=re.id,
            user_id=re.user_id,
            account_id=re.account_id,
            category_id=re.category_id,
            amount=str(re.amount),
            frequency=re.frequency.value if hasattr(re.frequency, "value") else str(re.frequency),
            next_date=str(re.next_date),
            description=re.description,
            status=re.status,
        )
