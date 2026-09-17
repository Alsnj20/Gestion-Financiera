from __future__ import annotations

from dataclasses import dataclass

from modules.notifications.application.dtos import (
    GetNotificationOutput,
    to_notification_output,
)
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetNotificationInput:
    notification_id: str
    requester_id: str
    requester_role: str = "USER"


class GetNotificationUseCase:
    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetNotificationInput) -> GetNotificationOutput:
        notification = await self._repo.find_by_id(inp.notification_id)

        if notification is None:
            raise NotFoundError(
                code="NOTIF_NOT_FOUND",
                message="Notificación no encontrada",
            )

        # Lectura: dueño o admin.
        if notification.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_notification_output(notification)
