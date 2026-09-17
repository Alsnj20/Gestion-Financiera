from __future__ import annotations

from dataclasses import dataclass

from modules.conversations.application.dtos import (
    ListConversationMessagesOutput,
    to_conversation_message_output,
)
from modules.conversations.application.ports.conversation_message_repository import (
    ConversationMessageRepositoryPort,
)
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListConversationMessagesInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListConversationMessagesUseCase:
    def __init__(self, repo: ConversationMessageRepositoryPort) -> None:
        self._repo = repo

    async def execute(
        self, inp: ListConversationMessagesInput
    ) -> list[ListConversationMessagesOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        items = await self._repo.find_by_user(inp.user_id)
        return [to_conversation_message_output(m) for m in items]
