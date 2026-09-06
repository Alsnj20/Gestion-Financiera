from __future__ import annotations
from shared.utils.uuids import is_uuid as _is_uuid

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.tag_mapper import to_domain, to_model
from infrastructure.database.models import TagModel
from modules.tags.domain.entities.tag import Tag
from modules.tags.application.ports.tag_repository import TagRepositoryPort
from shared.errors import ConflictError


class SqlAlchemyTagRepository(TagRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tag: Tag) -> None:
        existing = await self._session.get(TagModel, uuid.UUID(tag.id) if _is_uuid(tag.id) else None)
        if existing:
            existing.name = tag.name
        else:
            self._session.add(to_model(tag))
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictError(code="TAG_NAME_TAKEN", message=f"Tag ya existe: {tag.name}") from e

    async def find_by_id(self, tag_id: str) -> Tag | None:
        if not _is_uuid(tag_id):
            return None
        model = await self._session.get(TagModel, uuid.UUID(tag_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Tag]:
        if not _is_uuid(user_id):
            return []
        stmt = select(TagModel).where(TagModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        if not _is_uuid(user_id):
            return False
        stmt = select(TagModel.id).where(TagModel.user_id == uuid.UUID(user_id), TagModel.name == name.strip().lower()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None

    async def delete(self, entity_id: str) -> None:
        import uuid
        if not _is_uuid(entity_id):
            return
        model = await self._session.get(TagModel, uuid.UUID(entity_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()

