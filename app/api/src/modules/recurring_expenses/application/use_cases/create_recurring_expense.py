from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.recurring_expenses.application.dtos import (
    CreateRecurringExpenseOutput,
    to_recurring_expense_output,
)
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from modules.recurring_expenses.domain.entities.recurring_expense import (
    RecurringExpense,
)
from shared.errors import BusinessRuleError, NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class CreateRecurringExpenseInput:
    user_id: str
    account_id: str
    amount: Decimal
    frequency: str = "MONTHLY"
    next_date: date | None = None
    description: str = ""
    category_id: str = ""


async def _resolve_account(
    account_repo: AccountRepositoryPort, user_id: str, account_id: str
) -> str:
    if not account_id:
        raise ValidationError(
            code="RE_ACCOUNT_REQUIRED", message="account_id requerido"
        )
    account = await account_repo.find_by_id(account_id)
    if account is None:
        raise NotFoundError(
            code="RE_ACCOUNT_NOT_FOUND",
            message="Cuenta no encontrada",
        )
    if account.user_id != user_id:
        raise BusinessRuleError(
            code="FORBIDDEN",
            message="No autorizado",
        )
    return account.id


async def _resolve_category(
    category_repo: CategoryRepositoryPort, user_id: str, category_id: str
) -> str:
    if not category_id:
        return ""
    category = await category_repo.find_by_id(category_id)
    if category is None:
        raise NotFoundError(
            code="RE_CATEGORY_NOT_FOUND",
            message="Categoría no encontrada",
        )
    if category.user_id != user_id:
        raise BusinessRuleError(
            code="FORBIDDEN",
            message="No autorizado",
        )
    return category.id


class CreateRecurringExpenseUseCase:
    def __init__(
        self,
        repo: RecurringExpenseRepositoryPort,
        account_repo: AccountRepositoryPort,
        category_repo: CategoryRepositoryPort,
    ) -> None:
        self._repo = repo
        self._account_repo = account_repo
        self._category_repo = category_repo

    async def execute(
        self, inp: CreateRecurringExpenseInput
    ) -> CreateRecurringExpenseOutput:
        account_id = await _resolve_account(
            self._account_repo, inp.user_id, inp.account_id
        )
        category_id = await _resolve_category(
            self._category_repo, inp.user_id, inp.category_id
        )

        item = RecurringExpense.create(
            user_id=inp.user_id,
            account_id=account_id,
            amount=inp.amount,
            frequency=inp.frequency,
            next_date=inp.next_date,
            description=inp.description,
            category_id=category_id,
        )
        await self._repo.save(item)

        return to_recurring_expense_output(item)
