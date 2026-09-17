from __future__ import annotations

from typing import Protocol

from modules.conversations.domain.entities.conversation_message import (
    ConversationMessage,
)


class ConversationMessageRepositoryPort(Protocol):
    """Append-only: historial sin update ni delete en ningún nivel."""

    async def save(self, message: ConversationMessage) -> None: ...
    async def find_by_id(
        self, message_id: str, *, for_update: bool = False
    ) -> ConversationMessage | None: ...
    async def find_by_user(self, user_id: str) -> list[ConversationMessage]: ...
