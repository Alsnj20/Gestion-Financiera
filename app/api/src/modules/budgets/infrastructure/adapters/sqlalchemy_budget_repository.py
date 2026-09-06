from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.budget_mapper import to_domain, to_model
from infrastructure.database.models import BudgetModel
from modules.budgets.domain.entities.budget import Budget
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort


class SqlAlchemyBudgetRepository(BudgetRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, budget: Budget) -> None:
        existing = await self._session.get(BudgetModel, uuid.UUID(budget.id) if _is_uuid(budget.id) else None)
        if existing:
            existing.name = budget.name
            existing.amount = budget.amount
            existing.period_start = budget.period_start
            existing.period_end = budget.period_end
            existing.category_id = uuid.UUID(budget.category_id) if budget.category_id and _is_uuid(budget.category_id) else None
            existing.status = budget.status.value if hasattr(budget.status, "value") else str(budget.status)
        else:
            self._session.add(to_model(budget))
        await self._session.flush()

    async def find_by_id(self, budget_id: str) -> Budget | None:
        if not _is_uuid(budget_id):
            return None
        model = await self._session.get(BudgetModel, uuid.UUID(budget_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Budget]:
        if not _is_uuid(user_id):
            return []
        stmt = select(BudgetModel).where(BudgetModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
