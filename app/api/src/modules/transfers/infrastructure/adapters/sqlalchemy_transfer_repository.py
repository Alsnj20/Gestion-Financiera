from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.transfer_mapper import to_domain, to_model
from infrastructure.database.models import TransferModel
from modules.transfers.domain.entities.transfer import Transfer
from modules.transfers.application.ports.transfer_repository import TransferRepositoryPort
from shared.errors import ConflictError


class SqlAlchemyTransferRepository(TransferRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, transfer: Transfer) -> None:
        existing = await self._session.get(TransferModel, uuid.UUID(transfer.id) if _is_uuid(transfer.id) else None)
        if existing:
            existing.amount = transfer.amount
            existing.currency = transfer.currency
            existing.date = transfer.date
            existing.description = transfer.description
        else:
            self._session.add(to_model(transfer))
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictError(code="TRANSFER_CONFLICT", message=f"Conflicto al guardar transferencia") from e

    async def find_by_id(self, transfer_id: str) -> Transfer | None:
        if not _is_uuid(transfer_id):
            return None
        model = await self._session.get(TransferModel, uuid.UUID(transfer_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Transfer]:
        if not _is_uuid(user_id):
            return []
        stmt = select(TransferModel).where(TransferModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
