from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.notifications.application.dtos import (
    UpdateNotificationOutput,
    to_notification_output,
)
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateNotificationInput:
    notification_id: str
    user_id: str
    title: str | None = None
    message: str | None = None
    scheduled_at: datetime | None = None


class UpdateNotificationUseCase:
    """Solo metadatos y solo en PENDING: lo enviado no se reescribe."""

    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: UpdateNotificationInput) -> UpdateNotificationOutput:
        notification = await self._repo.find_by_id(inp.notification_id)

        if notification is None:
            raise NotFoundError(
                code="NOTIF_NOT_FOUND",
                message="Notificación no encontrada",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if notification.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        updated = notification.update_details(
            title=inp.title,
            message=inp.message,
            scheduled_at=inp.scheduled_at,
        )
        await self._repo.save(updated)

        return to_notification_output(updated)
