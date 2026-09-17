from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import BudgetModel
from modules.budgets.application.ports.budget_repository import BudgetRepositoryPort
from modules.budgets.domain.entities.budget import Budget
from modules.budgets.infrastructure.mappers.budget_mapper import to_domain, to_model
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyBudgetRepository(BudgetRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, budget: Budget) -> None:
        if not _is_uuid(budget.id):
            raise ValidationError(code="BUDGET_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(BudgetModel, uuid.UUID(budget.id))
        if existing:
            existing.name = budget.name
            existing.amount = budget.amount
            existing.period_start = budget.period_start
            existing.period_end = budget.period_end
            existing.category_id = (
                uuid.UUID(budget.category_id)
                if budget.category_id and _is_uuid(budget.category_id)
                else None
            )
            existing.status = (
                budget.status.value
                if hasattr(budget.status, "value")
                else str(budget.status)
            )
            existing.updated_at = budget.updated_at
        else:
            self._session.add(to_model(budget))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="BUDGET_CONFLICT", message="Conflicto al guardar presupuesto"
            ) from e

    async def find_by_id(
        self, budget_id: str, *, for_update: bool = False
    ) -> Budget | None:
        if not _is_uuid(budget_id):
            return None
        model = await self._session.get(
            BudgetModel,
            uuid.UUID(budget_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Budget]:
        if not _is_uuid(user_id):
            return []
        stmt = select(BudgetModel).where(BudgetModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]
