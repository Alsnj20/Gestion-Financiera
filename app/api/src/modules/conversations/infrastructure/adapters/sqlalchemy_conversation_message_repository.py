from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import ConversationMessageModel
from modules.conversations.application.ports.conversation_message_repository import (
    ConversationMessageRepositoryPort,
)
from modules.conversations.domain.entities.conversation_message import (
    ConversationMessage,
)
from modules.conversations.infrastructure.mappers.conversation_message_mapper import (
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyConversationMessageRepository(ConversationMessageRepositoryPort):
    """Append-only: historial sin update ni delete."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: ConversationMessage) -> None:
        if not _is_uuid(message.id):
            raise ValidationError(code="CM_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(
            ConversationMessageModel, uuid.UUID(message.id)
        )
        if existing is None:
            self._session.add(to_model(message))
        # Si ya existe (reintento con mismo id): no-op, append-only.
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="CM_CONFLICT", message="Conflicto al guardar mensaje"
            ) from e

    async def find_by_id(
        self, message_id: str, *, for_update: bool = False
    ) -> ConversationMessage | None:
        if not _is_uuid(message_id):
            return None
        model = await self._session.get(
            ConversationMessageModel,
            uuid.UUID(message_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[ConversationMessage]:
        if not _is_uuid(user_id):
            return []
        stmt = (
            select(ConversationMessageModel)
            .where(ConversationMessageModel.user_id == uuid.UUID(user_id))
            .order_by(ConversationMessageModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]
