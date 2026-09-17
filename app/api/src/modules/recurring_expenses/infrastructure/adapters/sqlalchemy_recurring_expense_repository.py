from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import RecurringExpenseModel
from modules.recurring_expenses.application.ports.recurring_expense_repository import (
    RecurringExpenseRepositoryPort,
)
from modules.recurring_expenses.domain.entities.recurring_expense import (
    RecurringExpense,
)
from modules.recurring_expenses.infrastructure.mappers.recurring_expense_mapper import (
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyRecurringExpenseRepository(RecurringExpenseRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, item: RecurringExpense) -> None:
        if not _is_uuid(item.id):
            raise ValidationError(code="RE_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(RecurringExpenseModel, uuid.UUID(item.id))
        if existing:
            existing.account_id = uuid.UUID(item.account_id)
            existing.category_id = (
                uuid.UUID(item.category_id)
                if item.category_id and _is_uuid(item.category_id)
                else None
            )
            existing.amount = item.amount
            existing.frequency = (
                item.frequency.value
                if hasattr(item.frequency, "value")
                else str(item.frequency)
            )
            existing.next_date = item.next_date
            existing.description = item.description
            existing.status = (
                item.status.value if hasattr(item.status, "value") else str(item.status)
            )
        else:
            self._session.add(to_model(item))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="RE_CONFLICT", message="Conflicto al guardar gasto recurrente"
            ) from e

    async def find_by_id(
        self, re_id: str, *, for_update: bool = False
    ) -> RecurringExpense | None:
        if not _is_uuid(re_id):
            return None
        model = await self._session.get(
            RecurringExpenseModel,
            uuid.UUID(re_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[RecurringExpense]:
        if not _is_uuid(user_id):
            return []
        stmt = select(RecurringExpenseModel).where(
            RecurringExpenseModel.user_id == uuid.UUID(user_id)
        )
        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]
