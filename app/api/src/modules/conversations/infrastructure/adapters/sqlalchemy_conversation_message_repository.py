from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.conversation_message_mapper import to_domain, to_model
from infrastructure.database.models import ConversationMessageModel
from modules.conversations.domain.entities.conversation_message import ConversationMessage
from modules.conversations.application.ports.conversation_message_repository import ConversationMessageRepositoryPort


class SqlAlchemyConversationMessageRepository(ConversationMessageRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: ConversationMessage) -> None:
        existing = await self._session.get(ConversationMessageModel, uuid.UUID(message.id) if _is_uuid(message.id) else None)
        if existing:
            existing.channel = message.channel.value if hasattr(message.channel, "value") else str(message.channel)
            existing.direction = message.direction.value if hasattr(message.direction, "value") else str(message.direction)
            existing.content = message.content
            existing.parsed_intent = message.parsed_intent
            existing.parsed_payload = message.parsed_payload
            existing.confidence = message.confidence
        else:
            self._session.add(to_model(message))
        await self._session.flush()

    async def find_by_id(self, message_id: str) -> ConversationMessage | None:
        if not _is_uuid(message_id):
            return None
        model = await self._session.get(ConversationMessageModel, uuid.UUID(message_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[ConversationMessage]:
        if not _is_uuid(user_id):
            return []
        stmt = select(ConversationMessageModel).where(ConversationMessageModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
