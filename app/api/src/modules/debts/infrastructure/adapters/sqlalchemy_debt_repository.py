from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import (
    DebtInstallmentModel,
    DebtModel,
    DebtPaymentModel,
)
from modules.debts.application.ports.debt_repository import DebtRepositoryPort
from modules.debts.domain.entities.debt import Debt, DebtInstallment, DebtPayment
from modules.debts.infrastructure.mappers.debt_mapper import (
    installment_to_domain,
    installment_to_model,
    payment_to_domain,
    payment_to_model,
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyDebtRepository(DebtRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, debt: Debt) -> None:
        if not _is_uuid(debt.id):
            raise ValidationError(code="DEBT_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(DebtModel, uuid.UUID(debt.id))
        if existing:
            existing.creditor_name = debt.creditor_name
            existing.principal_amount = debt.principal_amount
            existing.interest_rate = debt.interest_rate
            existing.interest_rate_type = (
                debt.interest_rate_type.value
                if hasattr(debt.interest_rate_type, "value")
                else str(debt.interest_rate_type)
            )
            existing.payment_frequency = (
                debt.payment_frequency.value
                if hasattr(debt.payment_frequency, "value")
                else str(debt.payment_frequency)
            )
            existing.installment_count = debt.installment_count
            existing.installment_amount = debt.installment_amount
            existing.start_date = debt.start_date
            existing.first_due_date = debt.first_due_date
            existing.amortization_method = (
                debt.amortization_method.value
                if hasattr(debt.amortization_method, "value")
                else str(debt.amortization_method)
            )
            existing.status = (
                debt.status.value if hasattr(debt.status, "value") else str(debt.status)
            )
            existing.notes = debt.notes
            existing.updated_at = debt.updated_at
        else:
            self._session.add(to_model(debt))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="DEBT_CONFLICT", message="Conflicto al guardar deuda"
            ) from e

    async def find_by_id(
        self, debt_id: str, *, for_update: bool = False
    ) -> Debt | None:
        if not _is_uuid(debt_id):
            return None
        model = await self._session.get(
            DebtModel,
            uuid.UUID(debt_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Debt]:
        if not _is_uuid(user_id):
            return []
        stmt = select(DebtModel).where(DebtModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def save_installments(self, installments: list[DebtInstallment]) -> None:
        for installment in installments:
            self._session.add(installment_to_model(installment))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="DEBT_CONFLICT", message="Conflicto al guardar cronograma"
            ) from e

    async def list_installments(self, debt_id: str) -> list[DebtInstallment]:
        if not _is_uuid(debt_id):
            return []
        stmt = (
            select(DebtInstallmentModel)
            .where(DebtInstallmentModel.debt_id == uuid.UUID(debt_id))
            .order_by(DebtInstallmentModel.installment_number.asc())
        )
        result = await self._session.execute(stmt)
        return [installment_to_domain(m) for m in result.scalars().all()]

    async def save_installment(self, installment: DebtInstallment) -> None:
        existing = await self._session.get(
            DebtInstallmentModel, uuid.UUID(installment.id)
        )
        if existing is None:
            self._session.add(installment_to_model(installment))
        else:
            existing.principal_paid = installment.principal_paid
            existing.interest_paid = installment.interest_paid
            existing.status = (
                installment.status.value
                if hasattr(installment.status, "value")
                else str(installment.status)
            )
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="DEBT_CONFLICT", message="Conflicto al guardar cuota"
            ) from e

    async def save_payment(self, payment: DebtPayment) -> None:
        self._session.add(payment_to_model(payment))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="DEBT_CONFLICT", message="Conflicto al guardar pago"
            ) from e

    async def list_payments(self, debt_id: str) -> list[DebtPayment]:
        if not _is_uuid(debt_id):
            return []
        stmt = (
            select(DebtPaymentModel)
            .where(DebtPaymentModel.debt_id == uuid.UUID(debt_id))
            .order_by(DebtPaymentModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [payment_to_domain(m) for m in result.scalars().all()]
