from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import NotificationModel
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from modules.notifications.domain.entities.notification import Notification
from modules.notifications.infrastructure.mappers.notification_mapper import (
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyNotificationRepository(NotificationRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, notification: Notification) -> None:
        if not _is_uuid(notification.id):
            raise ValidationError(code="NOTIF_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(
            NotificationModel, uuid.UUID(notification.id)
        )
        if existing:
            existing.type = notification.type
            existing.title = notification.title
            existing.message = notification.message
            existing.scheduled_at = notification.scheduled_at
            existing.sent_at = notification.sent_at
            existing.status = (
                notification.status.value
                if hasattr(notification.status, "value")
                else str(notification.status)
            )
            existing.related_entity_type = notification.related_entity_type
            existing.related_entity_id = notification.related_entity_id
        else:
            self._session.add(to_model(notification))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="NOTIF_CONFLICT", message="Conflicto al guardar notificación"
            ) from e

    async def find_by_id(
        self, notification_id: str, *, for_update: bool = False
    ) -> Notification | None:
        if not _is_uuid(notification_id):
            return None
        model = await self._session.get(
            NotificationModel,
            uuid.UUID(notification_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Notification]:
        if not _is_uuid(user_id):
            return []
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.user_id == uuid.UUID(user_id))
            .order_by(NotificationModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]

    async def delete(self, notification_id: str) -> None:
        if not _is_uuid(notification_id):
            return
        model = await self._session.get(NotificationModel, uuid.UUID(notification_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()
