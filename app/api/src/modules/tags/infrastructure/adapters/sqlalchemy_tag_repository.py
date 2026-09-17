from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import TagModel
from modules.tags.application.ports.tag_repository import TagRepositoryPort
from modules.tags.domain.entities.tag import Tag, normalize_tag_name
from modules.tags.infrastructure.mappers.tag_mapper import to_domain, to_model
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyTagRepository(TagRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tag: Tag) -> None:
        if not _is_uuid(tag.id):
            raise ValidationError(code="TAG_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(TagModel, uuid.UUID(tag.id))
        if existing:
            existing.name = tag.name
        else:
            self._session.add(to_model(tag))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="TAG_NAME_TAKEN", message=f"Tag ya existe: {tag.name}"
            ) from e

    async def find_by_id(self, tag_id: str, *, for_update: bool = False) -> Tag | None:
        if not _is_uuid(tag_id):
            return None
        model = await self._session.get(
            TagModel,
            uuid.UUID(tag_id),
            with_for_update=True if for_update else None,
        )
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
        # Misma normalización que la entidad (lower + sin #).
        normalized = normalize_tag_name(name)
        if not normalized:
            return False
        stmt = (
            select(TagModel.id)
            .where(
                TagModel.user_id == uuid.UUID(user_id),
                TagModel.name == normalized,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None

    async def delete(self, tag_id: str) -> None:
        if not _is_uuid(tag_id):
            return
        model = await self._session.get(TagModel, uuid.UUID(tag_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()
