from __future__ import annotations
from shared.utils.uuids import is_uuid as _is_uuid

import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.mappers.payment_method_mapper import to_domain, to_model
from infrastructure.database.models import PaymentMethodModel
from modules.payment_methods.domain.entities.payment_method import PaymentMethod
from modules.payment_methods.application.ports.payment_method_repository import PaymentMethodRepositoryPort
from shared.errors import ConflictError


class SqlAlchemyPaymentMethodRepository(PaymentMethodRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, payment_method: PaymentMethod) -> None:
        existing = await self._session.get(PaymentMethodModel, uuid.UUID(payment_method.id) if _is_uuid(payment_method.id) else None)
        if existing:
            existing.name = payment_method.name
            existing.type = payment_method.type
            existing.is_default = payment_method.is_default
            existing.status = payment_method.status.value if hasattr(payment_method.status, "value") else str(payment_method.status)
            existing.updated_at = payment_method.updated_at
        else:
            self._session.add(to_model(payment_method))
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise ConflictError(code="PM_NAME_TAKEN", message=f"Método de pago ya existe: {payment_method.name}") from e

    async def find_by_id(self, pm_id: str) -> PaymentMethod | None:
        if not _is_uuid(pm_id):
            return None
        model = await self._session.get(PaymentMethodModel, uuid.UUID(pm_id))
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[PaymentMethod]:
        if not _is_uuid(user_id):
            return []
        stmt = select(PaymentMethodModel).where(PaymentMethodModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def find_by_account(self, account_id: str) -> list[PaymentMethod]:
        if not _is_uuid(account_id):
            return []
        stmt = select(PaymentMethodModel).where(PaymentMethodModel.account_id == uuid.UUID(account_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        if not _is_uuid(user_id):
            return False
        stmt = select(PaymentMethodModel.id).where(PaymentMethodModel.user_id == uuid.UUID(user_id), PaymentMethodModel.name == name.strip()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None

    async def delete(self, entity_id: str) -> None:
        import uuid
        if not _is_uuid(entity_id):
            return
        model = await self._session.get(PaymentMethodModel, uuid.UUID(entity_id))
        if model:
            await self._session.delete(model)
            await self._session.flush()

