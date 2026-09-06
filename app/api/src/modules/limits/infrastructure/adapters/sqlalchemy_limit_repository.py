from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.limit_mapper import to_domain, to_model
from infrastructure.database.models import LimitModel
from modules.limits.domain.entities.limit import Limit
from modules.limits.application.ports.limit_repository import LimitRepositoryPort


class SqlAlchemyLimitRepository(LimitRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, limit: Limit) -> None:
        existing = await self._session.get(LimitModel, uuid.UUID(limit.id) if _is_uuid(limit.id) else None)
        if existing:
            existing.name = limit.name
            existing.amount = limit.amount
            existing.period_type = limit.period_type.value if hasattr(limit.period_type, "value") else str(limit.period_type)
            existing.category_id = uuid.UUID(limit.category_id) if limit.category_id and _is_uuid(limit.category_id) else None
            existing.threshold_warning = limit.threshold_warning
            existing.status = limit.status.value if hasattr(limit.status, "value") else str(limit.status)
        else:
            self._session.add(to_model(limit))
        await self._session.flush()

    async def find_by_id(self, limit_id: str) -> Limit | None:
        if not _is_uuid(limit_id):
            return None
        model = await self._session.get(LimitModel, uuid.UUID(limit_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Limit]:
        if not _is_uuid(user_id):
            return []
        stmt = select(LimitModel).where(LimitModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def delete(self, entity_id: str) -> None:
        import uuid
        if not _is_uuid(entity_id):
            return
        model = await self._session.get(LimitModel, uuid.UUID(entity_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
