from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import NotificationStatus

MAX_TITLE_LEN = 200
MAX_MSG_LEN = 1000
MAX_TYPE_LEN = 40
MAX_RELATED_TYPE_LEN = 40
MAX_RELATED_ID_LEN = 80


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="NOTIF_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_title(title: object) -> str:
    text = clean_str(title)
    if not text:
        raise ValidationError(code="NOTIF_TITLE_REQUIRED", message="title requerido")
    if len(text) > MAX_TITLE_LEN:
        raise ValidationError(
            code="NOTIF_TITLE_TOO_LONG", message=f"title excede {MAX_TITLE_LEN}"
        )
    return text


def _validate_message(message: object) -> str:
    text = clean_str(message)
    if not text:
        raise ValidationError(
            code="NOTIF_MESSAGE_REQUIRED", message="message requerido"
        )
    if len(text) > MAX_MSG_LEN:
        raise ValidationError(
            code="NOTIF_MESSAGE_TOO_LONG", message=f"message excede {MAX_MSG_LEN}"
        )
    return text


@dataclass(slots=True, frozen=True)
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
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(
                code="NOTIF_USER_REQUIRED", message="user_id requerido"
            )
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(
            self, "type", clean_str(self.type, "GENERAL")[:MAX_TYPE_LEN] or "GENERAL"
        )
        object.__setattr__(self, "title", _validate_title(self.title))
        object.__setattr__(self, "message", _validate_message(self.message))
        object.__setattr__(
            self,
            "related_entity_type",
            clean_str(self.related_entity_type)[:MAX_RELATED_TYPE_LEN],
        )
        object.__setattr__(
            self,
            "related_entity_id",
            clean_str(self.related_entity_id)[:MAX_RELATED_ID_LEN],
        )
        object.__setattr__(self, "status", NotificationStatus.safe(self.status))
        if not isinstance(self.scheduled_at, datetime):
            object.__setattr__(self, "scheduled_at", _utcnow())
        if self.sent_at is not None and not isinstance(self.sent_at, datetime):
            object.__setattr__(self, "sent_at", None)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        type: str = "GENERAL",
        title: str = "",
        message: str = "",
        scheduled_at: datetime | None = None,
        related_entity_type: str = "",
        related_entity_id: str = "",
    ) -> Notification:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            scheduled_at=scheduled_at or now,
            sent_at=None,
            status=NotificationStatus.PENDING,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            created_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        type: object = "GENERAL",
        title: object = "",
        message: object = "",
        scheduled_at: object = None,
        sent_at: object = None,
        status: object = NotificationStatus.PENDING,
        related_entity_type: object = "",
        related_entity_id: object = "",
        created_at: object = None,
    ) -> Notification:
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            type=clean_str(type, "GENERAL"),
            title=clean_str(title, ""),
            message=clean_str(message, ""),
            scheduled_at=scheduled_at
            if isinstance(scheduled_at, datetime)
            else _utcnow(),
            sent_at=sent_at if isinstance(sent_at, datetime) else None,
            status=NotificationStatus.safe(status),
            related_entity_type=clean_str(related_entity_type, ""),
            related_entity_id=clean_str(related_entity_id, ""),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
        )

    def is_pending(self) -> bool:
        return self.status == NotificationStatus.PENDING

    def update_details(
        self,
        *,
        title: str | None = None,
        message: str | None = None,
        scheduled_at: datetime | None = None,
    ) -> Notification:
        """Solo metadatos y solo en PENDING: lo enviado no se reescribe."""
        self._ensure_pending("editarse")
        return self._with(
            title=_validate_title(title) if title is not None else self.title,
            message=_validate_message(message) if message is not None else self.message,
            scheduled_at=scheduled_at
            if scheduled_at is not None
            else self.scheduled_at,
        )

    def mark_sent(self) -> Notification:
        if not self.is_pending():
            raise BusinessRuleError(
                code="NOTIF_NOT_PENDING",
                message="Solo se puede enviar una notificación pendiente.",
            )
        return self._with(sent_at=_utcnow(), status=NotificationStatus.SENT)

    def mark_failed(self) -> Notification:
        if not self.is_pending():
            raise BusinessRuleError(
                code="NOTIF_NOT_PENDING",
                message="Solo puede fallar una notificación pendiente.",
            )
        return self._with(status=NotificationStatus.FAILED)

    def cancel(self) -> Notification:
        if not self.is_pending():
            raise BusinessRuleError(
                code="NOTIF_NOT_PENDING",
                message="Solo se puede cancelar una notificación pendiente.",
            )
        return self._with(status=NotificationStatus.CANCELLED)

    def _ensure_pending(self, action_description: str) -> None:
        if not self.is_pending():
            raise BusinessRuleError(
                code="NOTIF_NOT_PENDING",
                message=f"Notificación no pendiente no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> Notification:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "scheduled_at": self.scheduled_at,
            "sent_at": self.sent_at,
            "status": self.status,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "created_at": self.created_at,
        }
        data.update(kwargs)
        return Notification(**data)  # type: ignore[arg-type]
