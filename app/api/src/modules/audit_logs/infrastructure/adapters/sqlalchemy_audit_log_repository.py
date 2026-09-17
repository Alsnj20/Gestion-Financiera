from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import AuditLogModel
from modules.audit_logs.application.ports.audit_log_repository import (
    AuditLogRepositoryPort,
)
from modules.audit_logs.domain.entities.audit_log import AuditLog
from modules.audit_logs.infrastructure.mappers.audit_log_mapper import (
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyAuditLogRepository(AuditLogRepositoryPort):
    """Append-only: sin update ni delete."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, log: AuditLog) -> None:
        if not _is_uuid(log.id):
            raise ValidationError(code="AL_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(AuditLogModel, uuid.UUID(log.id))
        if existing is None:
            self._session.add(to_model(log))
        # Si ya existe (reintento con mismo id): no-op, append-only.
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="AL_CONFLICT", message="Conflicto al guardar auditoría"
            ) from e

    async def find_by_id(
        self, audit_log_id: str, *, for_update: bool = False
    ) -> AuditLog | None:
        if not _is_uuid(audit_log_id):
            return None
        model = await self._session.get(
            AuditLogModel,
            uuid.UUID(audit_log_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[AuditLog]:
        if not _is_uuid(user_id):
            return []
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.user_id == uuid.UUID(user_id))
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]
