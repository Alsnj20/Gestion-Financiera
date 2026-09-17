from __future__ import annotations

from dataclasses import dataclass

from modules.notifications.application.dtos import (
    NotificationOutput as SendNotificationOutput,
)
from modules.notifications.application.dtos import to_notification_output
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class SendNotificationInput:
    notification_id: str
    user_id: str


class SendNotificationUseCase:
    """Transición PENDING → SENT (el envío real lo hace el provider)."""

    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: SendNotificationInput) -> SendNotificationOutput:
        notification = await self._repo.find_by_id(inp.notification_id, for_update=True)

        if notification is None:
            raise NotFoundError(
                code="NOTIF_NOT_FOUND",
                message="Notificación no encontrada",
            )

        if notification.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        sent = notification.mark_sent()
        await self._repo.save(sent)

        return to_notification_output(sent)
