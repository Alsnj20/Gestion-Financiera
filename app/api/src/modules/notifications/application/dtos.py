"""DTOs de salida unificados del módulo notifications.

Fuente única: `NotificationOutput` + `to_notification_output`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.notifications.domain.entities.notification import Notification


@dataclass(frozen=True, slots=True)
class NotificationOutput:
    id: str
    user_id: str
    type: str
    title: str
    message: str
    scheduled_at: datetime
    sent_at: datetime | None
    status: str


def to_notification_output(notification: Notification) -> NotificationOutput:
    return NotificationOutput(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        scheduled_at=notification.scheduled_at,
        sent_at=notification.sent_at,
        status=notification.status.value,
    )


# Aliases de compatibilidad.
CreateNotificationOutput = NotificationOutput
GetNotificationOutput = NotificationOutput
ListNotificationsOutput = NotificationOutput
UpdateNotificationOutput = NotificationOutput
