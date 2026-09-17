from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.notifications.application.dtos import (
    CreateNotificationOutput,
    to_notification_output,
)
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from modules.notifications.domain.entities.notification import Notification


@dataclass(frozen=True, slots=True)
class CreateNotificationInput:
    user_id: str
    type: str
    title: str
    message: str
    scheduled_at: datetime | None = None
    related_entity_type: str = ""
    related_entity_id: str = ""


class CreateNotificationUseCase:
    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateNotificationInput) -> CreateNotificationOutput:
        notification = Notification.create(
            user_id=inp.user_id,
            type=inp.type,
            title=inp.title,
            message=inp.message,
            scheduled_at=inp.scheduled_at,
            related_entity_type=inp.related_entity_type,
            related_entity_id=inp.related_entity_id,
        )
        await self._repo.save(notification)

        return to_notification_output(notification)
