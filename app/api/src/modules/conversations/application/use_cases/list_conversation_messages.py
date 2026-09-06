from __future__ import annotations

from dataclasses import dataclass
from modules.conversations.domain.entities.conversation_message import ConversationMessage
from modules.conversations.application.ports.conversation_message_repository import ConversationMessageRepositoryPort


@dataclass(frozen=True, slots=True)
class ListConversationMessagesInput:
    user_id: str


@dataclass(frozen=True, slots=True)
class ListConversationMessagesOutput:
    id: str
    user_id: str
    channel: str
    external_message_id: str
    direction: str
    content: str
    parsed_intent: str


class ListConversationMessagesUseCase:
    def __init__(self, repo: ConversationMessageRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListConversationMessagesInput) -> list[ListConversationMessagesOutput]:
        items = await self._repo.find_by_user(inp.user_id)
        return [
            ListConversationMessagesOutput(
                id=m.id,
                user_id=m.user_id,
                channel=m.channel.value if hasattr(m.channel, "value") else str(m.channel),
                external_message_id=m.external_message_id,
                direction=m.direction.value if hasattr(m.direction, "value") else str(m.direction),
                content=m.content,
                parsed_intent=m.parsed_intent,
            )
            for m in items
        ]
