"""DTOs de salida unificados del módulo conversations.

Fuente única: `ConversationMessageOutput` + `to_conversation_message_output`.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.conversations.domain.entities.conversation_message import (
    ConversationMessage,
)


@dataclass(frozen=True, slots=True)
class ConversationMessageOutput:
    id: str
    user_id: str
    channel: str
    external_message_id: str
    direction: str
    content: str
    parsed_intent: str


def to_conversation_message_output(
    msg: ConversationMessage,
) -> ConversationMessageOutput:
    return ConversationMessageOutput(
        id=msg.id,
        user_id=msg.user_id,
        channel=msg.channel.value,
        external_message_id=msg.external_message_id,
        direction=msg.direction.value,
        content=msg.content,
        parsed_intent=msg.parsed_intent,
    )


# Aliases de compatibilidad.
CreateConversationMessageOutput = ConversationMessageOutput
ListConversationMessagesOutput = ConversationMessageOutput
