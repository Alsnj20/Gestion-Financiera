"""Mapper ConversationMessage DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/conversation_message_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import ConversationMessageModel
from modules.conversations.domain.entities.conversation_message import (
    ConversationMessage,
)
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: ConversationMessageModel) -> ConversationMessage:
    return ConversationMessage.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        channel=getattr(model, "channel", "DASHBOARD"),
        external_message_id=getattr(model, "external_message_id", ""),
        direction=getattr(model, "direction", "INBOUND"),
        content=getattr(model, "content", "") or "",
        parsed_intent=getattr(model, "parsed_intent", "") or "",
        parsed_payload=getattr(model, "parsed_payload", None),
        confidence=getattr(model, "confidence", None),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: ConversationMessage) -> ConversationMessageModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="CM_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="CM_USER_REQUIRED", message="user_id requerido")
    return ConversationMessageModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        channel=domain.channel.value
        if hasattr(domain.channel, "value")
        else str(domain.channel),
        external_message_id=domain.external_message_id,
        direction=domain.direction.value
        if hasattr(domain.direction, "value")
        else str(domain.direction),
        content=domain.content or "",
        parsed_intent=domain.parsed_intent,
        parsed_payload=domain.parsed_payload,
        confidence=domain.confidence,
        created_at=domain.created_at,
    )
