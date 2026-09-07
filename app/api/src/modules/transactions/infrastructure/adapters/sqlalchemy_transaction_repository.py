from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import TransactionModel
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transactions.domain.entities.transaction import Transaction
from modules.transactions.infrastructure.mappers.transaction_mapper import (
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyTransactionRepository(TransactionRepositoryPort):
    """Adaptador de salida (Outbound Adapter) para PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tx: Transaction) -> None:
        if not _is_uuid(tx.id):
            raise ValidationError(code="TX_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(TransactionModel, uuid.UUID(tx.id))
        if existing:
            # update completo: todos los campos mutables del agregado.
            existing.user_id = (
                uuid.UUID(tx.user_id) if _is_uuid(tx.user_id) else existing.user_id
            )
            existing.account_id = (
                uuid.UUID(tx.account_id)
                if _is_uuid(tx.account_id)
                else existing.account_id
            )
            existing.type = tx.type.value if hasattr(tx.type, "value") else str(tx.type)
            existing.amount = tx.amount
            existing.currency = tx.currency
            existing.transaction_date = tx.transaction_date
            existing.description = tx.description
            existing.category_id = (
                uuid.UUID(tx.category_id) if _is_uuid(tx.category_id) else None
            )
            existing.payment_method_id = (
                uuid.UUID(tx.payment_method_id)
                if _is_uuid(tx.payment_method_id)
                else None
            )
            existing.source = (
                tx.source.value if hasattr(tx.source, "value") else str(tx.source)
            )
            existing.status = (
                tx.status.value if hasattr(tx.status, "value") else str(tx.status)
            )
            existing.updated_at = tx.updated_at
        else:
            self._session.add(to_model(tx))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="TX_CONFLICT", message=f"Conflicto al guardar transacción: {tx.id}"
            ) from e

    async def find_by_id(
        self, tx_id: str, *, for_update: bool = False
    ) -> Transaction | None:
        if not _is_uuid(tx_id):
            return None
        model = await self._session.get(
            TransactionModel,
            uuid.UUID(tx_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def list_by_user(
        self,
        user_id: str,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: str | None = None,
        type: str | None = None,
    ) -> list[Transaction]:
        if not _is_uuid(user_id):
            return []

        stmt = select(TransactionModel).where(
            TransactionModel.user_id == uuid.UUID(user_id)
        )

        if from_date:
            stmt = stmt.where(TransactionModel.transaction_date >= from_date)
        if to_date:
            stmt = stmt.where(TransactionModel.transaction_date <= to_date)
        if account_id and _is_uuid(account_id):
            stmt = stmt.where(TransactionModel.account_id == uuid.UUID(account_id))
        if type:
            stmt = stmt.where(TransactionModel.type == type.upper())

        stmt = stmt.order_by(TransactionModel.transaction_date.desc())

        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]
