from __future__ import annotations

import uuid

from infrastructure.database.models import ConversationMessageModel
from modules.conversations.domain.entities.conversation_message import (
    ConversationMessage,
)
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: ConversationMessageModel) -> ConversationMessage:
    return ConversationMessage(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        channel=getattr(model, "channel", "DASHBOARD"),
        external_message_id=getattr(model, "external_message_id", ""),
        direction=getattr(model, "direction", "INBOUND"),
        content=getattr(model, "content", ""),
        parsed_intent=getattr(model, "parsed_intent", ""),
        parsed_payload=getattr(model, "parsed_payload", None),
        confidence=getattr(model, "confidence", None),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: ConversationMessage) -> ConversationMessageModel:
    return ConversationMessageModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        channel=domain.channel.value
        if hasattr(domain.channel, "value")
        else str(domain.channel),
        external_message_id=domain.external_message_id,
        direction=domain.direction.value
        if hasattr(domain.direction, "value")
        else str(domain.direction),
        content=domain.content,
        parsed_intent=domain.parsed_intent,
        parsed_payload=domain.parsed_payload,
        confidence=domain.confidence,
        created_at=domain.created_at,
    )
