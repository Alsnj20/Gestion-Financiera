from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.conversations.application.dtos import (
    CreateConversationMessageOutput,
    to_conversation_message_output,
)
from modules.conversations.application.ports.conversation_message_repository import (
    ConversationMessageRepositoryPort,
)
from modules.conversations.domain.entities.conversation_message import (
    ConversationMessage,
)


@dataclass(frozen=True, slots=True)
class CreateConversationMessageInput:
    user_id: str
    channel: str = "DASHBOARD"
    external_message_id: str = ""
    direction: str = "INBOUND"
    content: str = ""
    parsed_intent: str = ""
    parsed_payload: dict | None = None
    confidence: Decimal | float | None = None


class CreateConversationMessageUseCase:
    def __init__(self, repo: ConversationMessageRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: CreateConversationMessageInput
    ) -> CreateConversationMessageOutput:
        msg = ConversationMessage.create(
            user_id=inp.user_id,
            channel=inp.channel,
            external_message_id=inp.external_message_id,
            direction=inp.direction,
            content=inp.content,
            parsed_intent=inp.parsed_intent,
            parsed_payload=inp.parsed_payload,
            confidence=inp.confidence,
        )
        await self._repo.save(msg)

        return to_conversation_message_output(msg)
