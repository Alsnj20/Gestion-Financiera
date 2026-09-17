"""DTOs de salida unificados del módulo recurring_expenses.

Fuente única: `RecurringExpenseOutput` + `to_recurring_expense_output`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.recurring_expenses.domain.entities.recurring_expense import (
    RecurringExpense,
)


@dataclass(frozen=True, slots=True)
class RecurringExpenseOutput:
    id: str
    user_id: str
    account_id: str
    category_id: str
    amount: Decimal
    frequency: str
    next_date: date
    description: str
    status: str


def to_recurring_expense_output(item: RecurringExpense) -> RecurringExpenseOutput:
    return RecurringExpenseOutput(
        id=item.id,
        user_id=item.user_id,
        account_id=item.account_id,
        category_id=item.category_id,
        amount=item.amount,
        frequency=item.frequency.value,
        next_date=item.next_date,
        description=item.description,
        status=item.status.value,
    )


# Aliases de compatibilidad.
CreateRecurringExpenseOutput = RecurringExpenseOutput
GetRecurringExpenseOutput = RecurringExpenseOutput
ListRecurringExpensesOutput = RecurringExpenseOutput
UpdateRecurringExpenseOutput = RecurringExpenseOutput
