from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.recurring_expense_mapper import to_domain, to_model
from infrastructure.database.models import RecurringExpenseModel
from modules.recurring_expenses.domain.entities.recurring_expense import RecurringExpense
from modules.recurring_expenses.application.ports.recurring_expense_repository import RecurringExpenseRepositoryPort


class SqlAlchemyRecurringExpenseRepository(RecurringExpenseRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, recurring_expense: RecurringExpense) -> None:
        existing = await self._session.get(RecurringExpenseModel, uuid.UUID(recurring_expense.id) if _is_uuid(recurring_expense.id) else None)
        if existing:
            existing.account_id = uuid.UUID(recurring_expense.account_id) if _is_uuid(recurring_expense.account_id) else existing.account_id
            existing.category_id = uuid.UUID(recurring_expense.category_id) if _is_uuid(recurring_expense.category_id) else None
            existing.amount = recurring_expense.amount
            existing.frequency = recurring_expense.frequency.value if hasattr(recurring_expense.frequency, "value") else str(recurring_expense.frequency)
            existing.next_date = recurring_expense.next_date
            existing.description = recurring_expense.description
            existing.status = recurring_expense.status
        else:
            self._session.add(to_model(recurring_expense))
        await self._session.flush()

    async def find_by_id(self, recurring_expense_id: str) -> RecurringExpense | None:
        if not _is_uuid(recurring_expense_id):
            return None
        model = await self._session.get(RecurringExpenseModel, uuid.UUID(recurring_expense_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[RecurringExpense]:
        if not _is_uuid(user_id):
            return []
        stmt = select(RecurringExpenseModel).where(RecurringExpenseModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
