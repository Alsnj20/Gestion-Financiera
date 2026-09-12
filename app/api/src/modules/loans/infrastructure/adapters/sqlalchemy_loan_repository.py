from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import (
    LoanInstallmentModel,
    LoanModel,
    LoanPaymentModel,
)
from modules.loans.application.ports.loan_repository import LoanRepositoryPort
from modules.loans.domain.entities.loan import Loan, LoanInstallment, LoanPayment
from modules.loans.infrastructure.mappers.loan_mapper import (
    installment_to_domain,
    installment_to_model,
    payment_to_domain,
    payment_to_model,
    to_domain,
    to_model,
)
from shared.errors import ConflictError, ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


class SqlAlchemyLoanRepository(LoanRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, loan: Loan) -> None:
        if not _is_uuid(loan.id):
            raise ValidationError(code="LOAN_ID_REQUIRED", message="id requerido")
        existing = await self._session.get(LoanModel, uuid.UUID(loan.id))
        if existing:
            existing.borrower_name = loan.borrower_name
            existing.principal_amount = loan.principal_amount
            existing.interest_rate = loan.interest_rate
            existing.interest_rate_type = (
                loan.interest_rate_type.value
                if hasattr(loan.interest_rate_type, "value")
                else str(loan.interest_rate_type)
            )
            existing.payment_frequency = (
                loan.payment_frequency.value
                if hasattr(loan.payment_frequency, "value")
                else str(loan.payment_frequency)
            )
            existing.installment_count = loan.installment_count
            existing.installment_amount = loan.installment_amount
            existing.start_date = loan.start_date
            existing.first_due_date = loan.first_due_date
            existing.amortization_method = (
                loan.amortization_method.value
                if hasattr(loan.amortization_method, "value")
                else str(loan.amortization_method)
            )
            existing.status = (
                loan.status.value if hasattr(loan.status, "value") else str(loan.status)
            )
            existing.notes = loan.notes
            existing.updated_at = loan.updated_at
        else:
            self._session.add(to_model(loan))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="LOAN_CONFLICT", message="Conflicto al guardar préstamo"
            ) from e

    async def find_by_id(
        self, loan_id: str, *, for_update: bool = False
    ) -> Loan | None:
        if not _is_uuid(loan_id):
            return None
        model = await self._session.get(
            LoanModel,
            uuid.UUID(loan_id),
            with_for_update=True if for_update else None,
        )
        return to_domain(model) if model else None

    async def find_by_user(self, user_id: str) -> list[Loan]:
        if not _is_uuid(user_id):
            return []
        stmt = select(LoanModel).where(LoanModel.user_id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        return [to_domain(m) for m in result.scalars().all()]

    async def save_installments(self, installments: list[LoanInstallment]) -> None:
        for installment in installments:
            self._session.add(installment_to_model(installment))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="LOAN_CONFLICT", message="Conflicto al guardar cronograma"
            ) from e

    async def list_installments(self, loan_id: str) -> list[LoanInstallment]:
        if not _is_uuid(loan_id):
            return []
        stmt = (
            select(LoanInstallmentModel)
            .where(LoanInstallmentModel.loan_id == uuid.UUID(loan_id))
            .order_by(LoanInstallmentModel.installment_number.asc())
        )
        result = await self._session.execute(stmt)
        return [installment_to_domain(m) for m in result.scalars().all()]

    async def save_installment(self, installment: LoanInstallment) -> None:
        existing = await self._session.get(
            LoanInstallmentModel, uuid.UUID(installment.id)
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
                code="LOAN_CONFLICT", message="Conflicto al guardar cuota"
            ) from e

    async def save_payment(self, payment: LoanPayment) -> None:
        self._session.add(payment_to_model(payment))
        try:
            await self._session.flush()
        except IntegrityError as e:
            raise ConflictError(
                code="LOAN_CONFLICT", message="Conflicto al guardar pago"
            ) from e

    async def list_payments(self, loan_id: str) -> list[LoanPayment]:
        if not _is_uuid(loan_id):
            return []
        stmt = (
            select(LoanPaymentModel)
            .where(LoanPaymentModel.loan_id == uuid.UUID(loan_id))
            .order_by(LoanPaymentModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [payment_to_domain(m) for m in result.scalars().all()]
