from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.account_mapper import to_domain, to_model
from infrastructure.database.models import AccountModel
from modules.accounts.domain.entities.account import Account
from shared.errors import ConflictError


class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, account: Account) -> None:
        existing = await self._session.get(AccountModel, uuid.UUID(account.id) if _is_uuid(account.id) else None)
        if existing:
            # update simple: re-mapea campos
            existing.name = account.name
            existing.type = account.type.value if hasattr(account.type, "value") else str(account.type)
            existing.currency = account.currency
            existing.initial_balance = account.initial_balance
            existing.current_balance = account.current_balance
            existing.is_default = account.is_default
            existing.status = account.status.value if hasattr(account.status, "value") else str(account.status)
            existing.updated_at = account.updated_at
        else:
            self._session.add(to_model(account))
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictError(code="ACCOUNT_NAME_TAKEN", message=f"cuenta ya existe para user {account.user_id}: {account.name}") from e

    async def find_by_id(self, account_id: str) -> Account | None:
        if not _is_uuid(account_id):
            return None
        model = await self._session.get(AccountModel, uuid.UUID(account_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Account]:
        if not _is_uuid(user_id):
            return []
        stmt = select(AccountModel).where(AccountModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def find_default(self, user_id: str) -> Account | None:
        if not _is_uuid(user_id):
            return None
        stmt = select(AccountModel).where(AccountModel.user_id == uuid.UUID(user_id), AccountModel.is_default.is_(True)).limit(1)
        result = await self._session.execute(stmt)
        m = result.scalars().first()
        return to_domain(m) if m else None

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        if not _is_uuid(user_id):
            return False
        stmt = select(AccountModel.id).where(AccountModel.user_id == uuid.UUID(user_id), AccountModel.name == name.strip()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None

    async def delete(self, entity_id: str) -> None:
        import uuid
        if not _is_uuid(entity_id):
            return
        model = await self._session.get(AccountModel, uuid.UUID(entity_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()


def _is_uuid(v: str) -> bool:
    try:
        uuid.UUID(str(v))
        return True
    except Exception:
        return False
