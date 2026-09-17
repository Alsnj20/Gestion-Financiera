from __future__ import annotations

from dataclasses import dataclass

from modules.notifications.application.dtos import (
    NotificationOutput as CancelNotificationOutput,
)
from modules.notifications.application.dtos import to_notification_output
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class CancelNotificationInput:
    notification_id: str
    user_id: str


class CancelNotificationUseCase:
    """Transición PENDING → CANCELLED."""

    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CancelNotificationInput) -> CancelNotificationOutput:
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

        cancelled = notification.cancel()
        await self._repo.save(cancelled)

        return to_notification_output(cancelled)
