from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import RefreshSessionModel
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyRefreshSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: str, token_hash: str, expires_at: datetime) -> None:
        if not _is_uuid(user_id):
            raise ValueError(f"user_id inválido: {user_id!r}")
        self._session.add(
            RefreshSessionModel(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                token_hash=token_hash,
                created_at=datetime.now(UTC),
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def find_active(self, token_hash: str) -> dict | None:
        stmt = select(RefreshSessionModel).where(
            RefreshSessionModel.token_hash == token_hash,
            RefreshSessionModel.revoked_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model is None:
            return None
        return {
            "user_id": str(model.user_id),
            "token_hash": model.token_hash,
            "expires_at": model.expires_at,
        }

    async def revoke(self, token_hash: str, replaced_by: str | None = None) -> None:
        stmt = (
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.token_hash == token_hash,
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC), replaced_by=replaced_by)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: str) -> None:
        if not _is_uuid(user_id):
            return
        stmt = (
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.user_id == uuid.UUID(user_id),
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
        await self._session.flush()
