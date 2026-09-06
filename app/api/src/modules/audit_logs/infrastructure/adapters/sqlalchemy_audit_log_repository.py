from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.audit_log_mapper import to_domain, to_model
from infrastructure.database.models import AuditLogModel
from modules.audit_logs.domain.entities.audit_log import AuditLog
from modules.audit_logs.application.ports.audit_log_repository import AuditLogRepositoryPort


class SqlAlchemyAuditLogRepository(AuditLogRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, audit_log: AuditLog) -> None:
        existing = await self._session.get(AuditLogModel, uuid.UUID(audit_log.id) if _is_uuid(audit_log.id) else None)
        if existing:
            existing.entity_type = audit_log.entity_type
            existing.entity_id = audit_log.entity_id
            existing.action = audit_log.action
            existing.old_value = audit_log.old_value
            existing.new_value = audit_log.new_value
            existing.source = audit_log.source
        else:
            self._session.add(to_model(audit_log))
        await self._session.flush()

    async def find_by_id(self, audit_log_id: str) -> AuditLog | None:
        if not _is_uuid(audit_log_id):
            return None
        model = await self._session.get(AuditLogModel, uuid.UUID(audit_log_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[AuditLog]:
        if not _is_uuid(user_id):
            return []
        stmt = select(AuditLogModel).where(AuditLogModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
