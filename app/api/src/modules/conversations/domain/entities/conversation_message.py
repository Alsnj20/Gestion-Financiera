from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.errors import ValidationError
from shared.types.enums import Channel, MessageDirection

MAX_CONTENT_LEN = 5000
MAX_INTENT_LEN = 60


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="CM_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_confidence(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        confidence = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(
            code="CM_CONFIDENCE_INVALID", message="confidence inválido"
        )
    if confidence < Decimal(0) or confidence > Decimal(1):
        raise ValidationError(
            code="CM_CONFIDENCE_OUT_OF_RANGE",
            message="confidence debe estar entre 0 y 1",
        )
    return confidence


@dataclass(slots=True, frozen=True)
class ConversationMessage:
    """Append-only: historial de chat, sin update ni delete en ningún nivel."""

    id: str
    user_id: str
    channel: Channel
    external_message_id: str
    direction: MessageDirection
    content: str
    parsed_intent: str
    parsed_payload: dict | None
    confidence: Decimal | None
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="CM_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "channel", Channel.safe(self.channel))
        external_id = clean_str(self.external_message_id)
        if not external_id:
            raise ValidationError(
                code="CM_EXTERNAL_ID_REQUIRED", message="external_message_id requerido"
            )
        object.__setattr__(self, "external_message_id", external_id)
        object.__setattr__(self, "direction", MessageDirection.safe(self.direction))
        content = clean_str(self.content)
        if len(content) > MAX_CONTENT_LEN:
            raise ValidationError(
                code="CM_CONTENT_TOO_LONG", message=f"content excede {MAX_CONTENT_LEN}"
            )
        object.__setattr__(self, "content", content)
        intent = clean_str(self.parsed_intent)
        if len(intent) > MAX_INTENT_LEN:
            raise ValidationError(
                code="CM_INTENT_TOO_LONG",
                message=f"parsed_intent excede {MAX_INTENT_LEN}",
            )
        object.__setattr__(self, "parsed_intent", intent)
        object.__setattr__(self, "confidence", _validate_confidence(self.confidence))

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        channel: Channel | str = Channel.DASHBOARD,
        external_message_id: str,
        direction: MessageDirection | str = MessageDirection.INBOUND,
        content: str = "",
        parsed_intent: str = "",
        parsed_payload: dict | None = None,
        confidence: Decimal | float | None = None,
    ) -> ConversationMessage:
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            channel=Channel.safe(channel),
            external_message_id=external_message_id,
            direction=MessageDirection.safe(direction),
            content=content or "",
            parsed_intent=parsed_intent or "",
            parsed_payload=parsed_payload,
            confidence=confidence,
            created_at=_utcnow(),
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        channel: object = Channel.DASHBOARD,
        external_message_id: object = "",
        direction: object = MessageDirection.INBOUND,
        content: object = "",
        parsed_intent: object = "",
        parsed_payload: object = None,
        confidence: object = None,
        created_at: object = None,
    ) -> ConversationMessage:
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            channel=Channel.safe(channel),
            external_message_id=clean_str(external_message_id, ""),
            direction=MessageDirection.safe(direction),
            content=clean_str(content, ""),
            parsed_intent=clean_str(parsed_intent, ""),
            parsed_payload=parsed_payload if isinstance(parsed_payload, dict) else None,
            confidence=confidence,
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
        )
