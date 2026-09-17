from __future__ import annotations

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import PaymentMethodModel
from modules.payment_methods.application.ports.payment_method_repository import (
    PaymentMethodRepositoryPort,
)
from modules.payment_methods.domain.entities.payment_method import PaymentMethod
from modules.payment_methods.infrastructure.mappers.payment_method_mapper import (
    to_domain,
    to_model,
)
from shared.domain.guards import clean_str
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyPaymentMethodRepository(PaymentMethodRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, payment_method: PaymentMethod) -> None:
        if not _is_uuid(payment_method.id):
            raise ValidationError(code="PM_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(
            PaymentMethodModel, uuid.UUID(payment_method.id)
        )
        if existing:
            existing.name = payment_method.name
            existing.type = payment_method.type
            existing.account_id = uuid.UUID(payment_method.account_id)
            existing.is_default = payment_method.is_default
            existing.status = (
                payment_method.status.value
                if hasattr(payment_method.status, "value")
                else str(payment_method.status)
            )
            existing.updated_at = payment_method.updated_at
        else:
            self._session.add(to_model(payment_method))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="PM_NAME_TAKEN",
                message=f"Método de pago ya existe: {payment_method.name}",
            ) from e

    async def find_by_id(
        self, pm_id: str, *, for_update: bool = False
    ) -> PaymentMethod | None:
        if not _is_uuid(pm_id):
            return None
        model = await self._session.get(
            PaymentMethodModel,
            uuid.UUID(pm_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[PaymentMethod]:
        if not _is_uuid(user_id):
            return []
        stmt = (
            select(PaymentMethodModel)
            .where(PaymentMethodModel.user_id == uuid.UUID(user_id))
            .order_by(
                PaymentMethodModel.is_default.desc(),
                PaymentMethodModel.name.asc(),
            )
        )
        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]

    async def find_by_account(self, account_id: str) -> list[PaymentMethod]:
        if not _is_uuid(account_id):
            return []
        stmt = select(PaymentMethodModel).where(
            PaymentMethodModel.account_id == uuid.UUID(account_id)
        )
        result = await self._session.execute(stmt)
        return [to_domain(model) for model in result.scalars().all()]

    async def clear_default_for_user(self, user_id: str) -> None:
        if not _is_uuid(user_id):
            return
        stmt = (
            update(PaymentMethodModel)
            .where(
                PaymentMethodModel.user_id == uuid.UUID(user_id),
                PaymentMethodModel.is_default.is_(True),
            )
            .values(is_default=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        if not _is_uuid(user_id):
            return False
        normalized = clean_str(name)
        if not normalized:
            return False
        stmt = (
            select(PaymentMethodModel.id)
            .where(
                PaymentMethodModel.user_id == uuid.UUID(user_id),
                func.lower(PaymentMethodModel.name) == normalized.casefold(),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first() is not None
