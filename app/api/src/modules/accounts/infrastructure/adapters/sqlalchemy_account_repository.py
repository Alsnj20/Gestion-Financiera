from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import AccountModel
from modules.accounts.domain.entities.account import Account
from modules.accounts.infrastructure.mappers.account_mapper import to_domain, to_model
from shared.errors import ConflictError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, account: Account) -> None:
        account_id = uuid.UUID(account.id)
        existing = await self._session.get(AccountModel, account_id)

        if existing is not None:
            existing.name = account.name
            existing.type = account.type.value
            existing.currency = account.currency
            existing.initial_balance = account.initial_balance
            existing.current_balance = account.current_balance
            existing.is_default = account.is_default
            existing.status = account.status.value
            existing.updated_at = account.updated_at
        else:
            self._session.add(to_model(account))

        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ConflictError(
                code="ACCOUNT_CONFLICT",
                message="No se pudo guardar la cuenta.",
            ) from exc

    async def find_by_id(
        self, account_id: str, *, for_update: bool = False
    ) -> Account | None:
        if not _is_uuid(account_id):
            return None
        model = await self._session.get(
            AccountModel,
            uuid.UUID(account_id),
            with_for_update=True if for_update else None,
        )
        if model is None:
            return None
        return to_domain(model)

    async def find_by_user(self, user_id: str) -> list[Account]:
        if not _is_uuid(user_id):
            return []
        stmt = (
            select(AccountModel)
            .where(AccountModel.user_id == uuid.UUID(user_id))
            .order_by(
                AccountModel.is_default.desc(),
                AccountModel.name.asc(),
            )
        )

        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]

    async def clear_default_for_user(
        self,
        user_id: str,
    ) -> None:
        if not _is_uuid(user_id):
            return

        stmt = (
            update(AccountModel)
            .where(
                AccountModel.user_id == uuid.UUID(user_id),
                AccountModel.is_default.is_(True),
            )
            .values(is_default=False)
        )

        await self._session.execute(stmt)
        await self._session.flush()

    async def exists_name_for_user(
        self,
        user_id: str,
        name: str,
    ) -> bool:
        if not _is_uuid(user_id):
            return False

        normalized = (name or "").strip().casefold()
        if not normalized:
            return False

        stmt = (
            select(AccountModel.id)
            .where(
                AccountModel.user_id == uuid.UUID(user_id),
                func.lower(AccountModel.name) == normalized,
            )
            .limit(1)
        )

        result = await self._session.execute(stmt)
        return result.scalar() is not None
