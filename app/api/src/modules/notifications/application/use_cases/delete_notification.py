from __future__ import annotations

from dataclasses import dataclass

from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class DeleteNotificationInput:
    notification_id: str
    user_id: str


class DeleteNotificationUseCase:
    """Borrado físico: notificaciones efímeras sin referencias."""

    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: DeleteNotificationInput) -> None:
        notification = await self._repo.find_by_id(inp.notification_id)

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

        await self._repo.delete(notification.id)
