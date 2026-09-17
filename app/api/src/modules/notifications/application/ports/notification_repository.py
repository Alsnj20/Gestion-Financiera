from __future__ import annotations

from typing import Protocol

from modules.notifications.domain.entities.notification import Notification


class NotificationRepositoryPort(Protocol):
    """Notificaciones efímeras sin referencias: borrado físico permitido."""

    async def save(self, notification: Notification) -> None: ...
    async def find_by_id(
        self, notification_id: str, *, for_update: bool = False
    ) -> Notification | None: ...
    async def find_by_user(self, user_id: str) -> list[Notification]: ...
    async def delete(self, notification_id: str) -> None: ...
