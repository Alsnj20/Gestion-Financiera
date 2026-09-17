from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import LimitModel
from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from modules.limits.domain.entities.limit import Limit
from modules.limits.infrastructure.mappers.limit_mapper import to_domain, to_model
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyLimitRepository(LimitRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, limit: Limit) -> None:
        if not _is_uuid(limit.id):
            raise ValidationError(code="LIMIT_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(LimitModel, uuid.UUID(limit.id))
        if existing:
            existing.name = limit.name
            existing.amount = limit.amount
            existing.period_type = (
                limit.period_type.value
                if hasattr(limit.period_type, "value")
                else str(limit.period_type)
            )
            existing.category_id = (
                uuid.UUID(limit.category_id)
                if limit.category_id and _is_uuid(limit.category_id)
                else None
            )
            existing.threshold_warning = limit.threshold_warning
            existing.status = (
                limit.status.value
                if hasattr(limit.status, "value")
                else str(limit.status)
            )
            existing.updated_at = limit.updated_at
        else:
            self._session.add(to_model(limit))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="LIMIT_CONFLICT", message="Conflicto al guardar límite"
            ) from e

    async def find_by_id(
        self, limit_id: str, *, for_update: bool = False
    ) -> Limit | None:
        if not _is_uuid(limit_id):
            return None
        model = await self._session.get(
            LimitModel,
            uuid.UUID(limit_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Limit]:
        if not _is_uuid(user_id):
            return []
        stmt = select(LimitModel).where(LimitModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]
