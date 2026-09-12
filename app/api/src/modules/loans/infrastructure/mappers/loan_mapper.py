"""Mapper Loan DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/loan_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import (
    LoanInstallmentModel,
    LoanModel,
    LoanPaymentModel,
)
from modules.loans.domain.entities.loan import Loan, LoanInstallment, LoanPayment
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def _req_uuid(value: object, field: str) -> uuid.UUID:
    if not _is_uuid(value):
        raise ValidationError(code="LOAN_ID_REQUIRED", message=f"{field} inválido")
    return uuid.UUID(str(value))


def to_domain(model: LoanModel) -> Loan:
    return Loan.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        borrower_name=getattr(model, "borrower_name", ""),
        principal_amount=getattr(model, "principal_amount", 0),
        interest_rate=getattr(model, "interest_rate", 0),
        interest_rate_type=getattr(model, "interest_rate_type", "PERCENTAGE"),
        payment_frequency=getattr(model, "payment_frequency", "MONTHLY"),
        installment_count=getattr(model, "installment_count", 1),
        installment_amount=getattr(model, "installment_amount", 0),
        start_date=getattr(model, "start_date", None),
        first_due_date=getattr(model, "first_due_date", None),
        amortization_method=getattr(model, "amortization_method", "SIMPLE"),
        status=getattr(model, "status", "ACTIVE"),
        notes=getattr(model, "notes", ""),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Loan) -> LoanModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    return LoanModel(
        id=_req_uuid(domain.id, "id"),
        user_id=_req_uuid(domain.user_id, "user_id"),
        borrower_name=domain.borrower_name,
        principal_amount=domain.principal_amount,
        interest_rate=domain.interest_rate,
        interest_rate_type=domain.interest_rate_type.value
        if hasattr(domain.interest_rate_type, "value")
        else str(domain.interest_rate_type),
        payment_frequency=domain.payment_frequency.value
        if hasattr(domain.payment_frequency, "value")
        else str(domain.payment_frequency),
        installment_count=domain.installment_count,
        installment_amount=domain.installment_amount,
        start_date=domain.start_date,
        first_due_date=domain.first_due_date,
        amortization_method=domain.amortization_method.value
        if hasattr(domain.amortization_method, "value")
        else str(domain.amortization_method),
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        notes=domain.notes,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def installment_to_domain(model: LoanInstallmentModel) -> LoanInstallment:
    return LoanInstallment(
        id=str(model.id) if model.id else "",
        loan_id=str(model.loan_id) if model.loan_id else "",
        installment_number=getattr(model, "installment_number", 1),
        due_date=getattr(model, "due_date", None),
        principal_due=getattr(model, "principal_due", 0),
        interest_due=getattr(model, "interest_due", 0),
        total_due=getattr(model, "total_due", None),
        principal_paid=getattr(model, "principal_paid", 0),
        interest_paid=getattr(model, "interest_paid", 0),
        status=getattr(model, "status", "PENDING"),
        created_at=getattr(model, "created_at", None),
    )


def installment_to_model(domain: LoanInstallment) -> LoanInstallmentModel:
    return LoanInstallmentModel(
        id=_req_uuid(domain.id, "installment id"),
        loan_id=_req_uuid(domain.loan_id, "loan_id"),
        installment_number=domain.installment_number,
        due_date=domain.due_date,
        principal_due=domain.principal_due,
        interest_due=domain.interest_due,
        total_due=domain.total_due,
        principal_paid=domain.principal_paid,
        interest_paid=domain.interest_paid,
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
    )


def payment_to_domain(model: LoanPaymentModel) -> LoanPayment:
    return LoanPayment(
        id=str(model.id) if model.id else "",
        loan_id=str(model.loan_id) if model.loan_id else "",
        transaction_id=str(model.transaction_id) if model.transaction_id else "",
        payment_date=getattr(model, "payment_date", None),
        principal_amount=getattr(model, "principal_amount", 0),
        interest_amount=getattr(model, "interest_amount", 0),
        total_amount=getattr(model, "total_amount", None),
        installment_id=str(model.installment_id) if model.installment_id else "",
        created_at=getattr(model, "created_at", None),
    )


def payment_to_model(domain: LoanPayment) -> LoanPaymentModel:
    return LoanPaymentModel(
        id=_req_uuid(domain.id, "payment id"),
        loan_id=_req_uuid(domain.loan_id, "loan_id"),
        transaction_id=_req_uuid(domain.transaction_id, "transaction_id"),
        payment_date=domain.payment_date,
        principal_amount=domain.principal_amount,
        interest_amount=domain.interest_amount,
        total_amount=domain.total_amount,
        installment_id=uuid.UUID(domain.installment_id)
        if _is_uuid(domain.installment_id)
        else None,
        created_at=domain.created_at,
    )
