from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.category_mapper import to_domain, to_model
from infrastructure.database.models import CategoryModel
from modules.categories.domain.entities.category import Category
from modules.categories.application.ports.category_repository import CategoryRepositoryPort
from shared.errors import ConflictError


class SqlAlchemyCategoryRepository(CategoryRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, category: Category) -> None:
        existing = await self._session.get(CategoryModel, uuid.UUID(category.id) if _is_uuid(category.id) else None)
        if existing:
            existing.name = category.name
            existing.type = category.type.value if hasattr(category.type, "value") else str(category.type)
            existing.parent_id = uuid.UUID(category.parent_id) if category.parent_id and _is_uuid(category.parent_id) else None
            existing.status = category.status.value if hasattr(category.status, "value") else str(category.status)
            existing.updated_at = category.updated_at
        else:
            self._session.add(to_model(category))
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictError(code="CAT_NAME_TAKEN", message=f"Categoría ya existe: {category.name}") from e

    async def find_by_id(self, category_id: str) -> Category | None:
        if not _is_uuid(category_id):
            return None
        model = await self._session.get(CategoryModel, uuid.UUID(category_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Category]:
        if not _is_uuid(user_id):
            return []
        stmt = select(CategoryModel).where(CategoryModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        if not _is_uuid(user_id):
            return False
        stmt = select(CategoryModel.id).where(CategoryModel.user_id == uuid.UUID(user_id), CategoryModel.name == name.strip()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
