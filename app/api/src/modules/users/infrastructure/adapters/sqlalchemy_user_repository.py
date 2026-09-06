from __future__ import annotations
from shared.utils.uuids import is_uuid as _is_uuid

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.user_mapper import to_domain, to_model, update_model
from infrastructure.database.models import UserModel
from modules.users.domain.entities.user import User
from modules.users.domain.ports.user_repository import UserRepositoryPort
from shared.errors import ConflictError


class SqlAlchemyUserRepository(UserRepositoryPort):
    """Adaptador de salida (Outbound Adapter) para PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        existing = await self._session.get(UserModel, uuid.UUID(user.id) if _is_uuid(user.id) else None)
        if existing:
            update_model(existing, user)
        else:
            model = to_model(user)
            self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            msg = str(e.orig) if hasattr(e, "orig") else str(e)
            if "phone" in msg.lower() or "uq" in msg.lower():
                raise ConflictError(code="USER_PHONE_TAKEN", message=f"Teléfono ya existe: {user.phone}") from e
            raise ConflictError(code="USER_CONFLICT", message="Conflicto al guardar usuario") from e

    async def find_by_id(self, user_id: str) -> User | None:
        if not _is_uuid(user_id):
            return None
        model = await self._session.get(UserModel, uuid.UUID(user_id))
        return to_domain(model) if model else None

    async def find_by_phone(self, phone: str) -> User | None:
        stmt = select(UserModel).where(UserModel.phone == phone.strip())
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return to_domain(model) if model else None

    async def find_by_email(self, email: str) -> User | None:
        cleaned = email.strip().lower()
        if not cleaned or "@" not in cleaned:
            return None
        stmt = select(UserModel).where(UserModel.email == cleaned)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return to_domain(model) if model else None

    async def exists_by_phone(self, phone: str) -> bool:
        stmt = select(UserModel.id).where(UserModel.phone == phone.strip()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None

    async def list_all(self, limit: int = 100) -> list[User]:
        stmt = select(UserModel).order_by(UserModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def delete(self, entity_id: str) -> None:
        import uuid
        if not _is_uuid(entity_id):
            return
        model = await self._session.get(UserModel, uuid.UUID(entity_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()

