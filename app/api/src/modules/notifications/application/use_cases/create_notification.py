from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from modules.notifications.domain.entities.notification import Notification
from modules.notifications.application.ports.notification_repository import NotificationRepositoryPort


@dataclass(frozen=True, slots=True)
class CreateNotificationInput:
    user_id: str
    type: str
    title: str
    message: str
    scheduled_at: datetime | None = None
    related_entity_type: str = ""
    related_entity_id: str = ""


@dataclass(frozen=True, slots=True)
class CreateNotificationOutput:
    id: str
    user_id: str
    type: str
    title: str
    message: str
    status: str


class CreateNotificationUseCase:
    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateNotificationInput) -> CreateNotificationOutput:
        notification = Notification(
            id="", user_id=inp.user_id, type=inp.type, title=inp.title, message=inp.message,
            scheduled_at=inp.scheduled_at, related_entity_type=inp.related_entity_type,
            related_entity_id=inp.related_entity_id,
        )
        await self._repo.save(notification)

        return CreateNotificationOutput(
            id=notification.id, user_id=notification.user_id, type=notification.type,
            title=notification.title, message=notification.message,
            status=notification.status.value if hasattr(notification.status, "value") else str(notification.status),
        )
