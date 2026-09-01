from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.types.enums import NotificationStatus

MAX_TITLE_LEN = 200
MAX_MSG_LEN = 1000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class Notification:
    id: str
    user_id: str
    type: str
    title: str
    message: str
    scheduled_at: datetime = field(default_factory=_utcnow)
    sent_at: datetime | None = None
    status: NotificationStatus = NotificationStatus.PENDING
    related_entity_type: str = ""  # "" si no aplica
    related_entity_id: str = ""
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.type = _safe_str(self.type, "GENERAL") or "GENERAL"
        self.title = _safe_str(self.title, "Notification")[:MAX_TITLE_LEN]
        self.message = _safe_str(self.message, "")[:MAX_MSG_LEN]
        self.related_entity_type = _safe_str(self.related_entity_type, "")
        self.related_entity_id = _safe_str(self.related_entity_id, "")
        self.status = NotificationStatus.safe(self.status)
        if not isinstance(self.scheduled_at, datetime):
            self.scheduled_at = _utcnow()
        if self.sent_at is not None and not isinstance(self.sent_at, datetime):
            self.sent_at = None

    def mark_sent(self) -> Notification:
        now = _utcnow()
        return Notification(id=self.id, user_id=self.user_id, type=self.type, title=self.title, message=self.message, scheduled_at=self.scheduled_at, sent_at=now, status=NotificationStatus.SENT, related_entity_type=self.related_entity_type, related_entity_id=self.related_entity_id, created_at=self.created_at)
