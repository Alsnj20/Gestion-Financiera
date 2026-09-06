from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from shared.errors import ValidationError
from shared.types.enums import Channel, MessageDirection


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class ConversationMessage:
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
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.channel = Channel.safe(self.channel)
        self.external_message_id = _safe_str(self.external_message_id)
        self.direction = MessageDirection.safe(self.direction)
        self.content = _safe_str(self.content, "")
        self.parsed_intent = _safe_str(self.parsed_intent, "")
        self.confidence = self._safe_decimal(self.confidence)

        if not self.user_id:
            raise ValidationError(code="CM_USER_REQUIRED", message="user_id requerido")
        if not self.external_message_id:
            raise ValidationError(code="CM_EXTERNAL_ID_REQUIRED", message="external_message_id requerido")

    @staticmethod
    def _safe_decimal(v: object) -> Decimal | None:
        if v is None:
            return None
        try:
            d = Decimal(str(v))
            if d < Decimal("0") or d > Decimal("1"):
                return None
            return d
        except Exception:
            return None

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
        now = _utcnow()
        conf = None
        if confidence is not None:
            try:
                conf = Decimal(str(confidence))
                if conf < Decimal("0") or conf > Decimal("1"):
                    conf = None
            except Exception:
                conf = None
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            channel=Channel.safe(channel),
            external_message_id=external_message_id,
            direction=MessageDirection.safe(direction),
            content=content or "",
            parsed_intent=parsed_intent or "",
            parsed_payload=parsed_payload,
            confidence=conf,
            created_at=now,
        )

    @classmethod
    def rehydrate(cls, **kwargs: object) -> ConversationMessage:
        conf_raw = kwargs.get("confidence")
        conf = None
        if conf_raw is not None:
            try:
                conf = Decimal(str(conf_raw))
                if conf < Decimal("0") or conf > Decimal("1"):
                    conf = None
            except Exception:
                conf = None
        return cls(
            id=_safe_str(kwargs.get("id")) or str(uuid.uuid4()),
            user_id=_safe_str(kwargs.get("user_id"), ""),
            channel=Channel.safe(kwargs.get("channel")),
            external_message_id=_safe_str(kwargs.get("external_message_id"), ""),
            direction=MessageDirection.safe(kwargs.get("direction")),
            content=_safe_str(kwargs.get("content"), ""),
            parsed_intent=_safe_str(kwargs.get("parsed_intent"), ""),
            parsed_payload=kwargs.get("parsed_payload") if isinstance(kwargs.get("parsed_payload"), dict) else None,
            confidence=conf,
            created_at=kwargs.get("created_at") if isinstance(kwargs.get("created_at"), datetime) else _utcnow(),
        )
