from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.notification_mapper import to_domain, to_model
from infrastructure.database.models import NotificationModel
from modules.notifications.domain.entities.notification import Notification
from modules.notifications.application.ports.notification_repository import NotificationRepositoryPort


class SqlAlchemyNotificationRepository(NotificationRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, notification: Notification) -> None:
        existing = await self._session.get(NotificationModel, uuid.UUID(notification.id) if _is_uuid(notification.id) else None)
        if existing:
            existing.type = notification.type
            existing.title = notification.title
            existing.message = notification.message
            existing.scheduled_at = notification.scheduled_at
            existing.sent_at = notification.sent_at
            existing.status = notification.status.value if hasattr(notification.status, "value") else str(notification.status)
            existing.related_entity_type = notification.related_entity_type
            existing.related_entity_id = notification.related_entity_id
        else:
            self._session.add(to_model(notification))
        await self._session.flush()

    async def find_by_id(self, notification_id: str) -> Notification | None:
        if not _is_uuid(notification_id):
            return None
        model = await self._session.get(NotificationModel, uuid.UUID(notification_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Notification]:
        if not _is_uuid(user_id):
            return []
        stmt = select(NotificationModel).where(NotificationModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
