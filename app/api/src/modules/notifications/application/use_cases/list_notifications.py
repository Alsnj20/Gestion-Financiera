from __future__ import annotations

from dataclasses import dataclass

from modules.notifications.application.dtos import (
    ListNotificationsOutput,
    to_notification_output,
)
from modules.notifications.application.ports.notification_repository import (
    NotificationRepositoryPort,
)
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListNotificationsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListNotificationsUseCase:
    def __init__(self, repo: NotificationRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: ListNotificationsInput
    ) -> list[ListNotificationsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        notifications = await self._repo.find_by_user(inp.user_id)
        return [to_notification_output(n) for n in notifications]
