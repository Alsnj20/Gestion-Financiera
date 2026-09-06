from __future__ import annotations
from shared.utils.uuids import is_uuid as _is_uuid

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.debt_mapper import to_domain, to_model
from infrastructure.database.models import DebtModel
from modules.debts.domain.entities.debt import Debt
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from shared.errors import ConflictError


class SqlAlchemyDebtRepository(DebtRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, debt: Debt) -> None:
        existing = await self._session.get(DebtModel, uuid.UUID(debt.id) if _is_uuid(debt.id) else None)
        if existing:
            existing.creditor_name = debt.creditor_name
            existing.principal_amount = debt.principal_amount
            existing.interest_rate = debt.interest_rate
            existing.interest_rate_type = debt.interest_rate_type.value if hasattr(debt.interest_rate_type, "value") else str(debt.interest_rate_type)
            existing.payment_frequency = debt.payment_frequency.value if hasattr(debt.payment_frequency, "value") else str(debt.payment_frequency)
            existing.installment_count = debt.installment_count
            existing.installment_amount = debt.installment_amount
            existing.start_date = debt.start_date
            existing.first_due_date = debt.first_due_date
            existing.amortization_method = debt.amortization_method.value if hasattr(debt.amortization_method, "value") else str(debt.amortization_method)
            existing.status = debt.status.value if hasattr(debt.status, "value") else str(debt.status)
            existing.notes = debt.notes
            existing.updated_at = debt.updated_at
        else:
            self._session.add(to_model(debt))
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictError(code="DEBT_CONFLICT", message=f"Conflicto al guardar deuda") from e

    async def find_by_id(self, debt_id: str) -> Debt | None:
        if not _is_uuid(debt_id):
            return None
        model = await self._session.get(DebtModel, uuid.UUID(debt_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Debt]:
        if not _is_uuid(user_id):
            return []
        stmt = select(DebtModel).where(DebtModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def delete(self, entity_id: str) -> None:
        import uuid
        if not _is_uuid(entity_id):
            return
        model = await self._session.get(DebtModel, uuid.UUID(entity_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()

