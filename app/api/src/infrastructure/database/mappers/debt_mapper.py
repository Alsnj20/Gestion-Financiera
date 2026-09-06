from __future__ import annotations

import uuid

from infrastructure.database.models import DebtModel
from modules.debts.domain.entities.debt import Debt
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: DebtModel) -> Debt:
    return Debt.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        creditor_name=getattr(model, "creditor_name", ""),
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


def to_model(domain: Debt) -> DebtModel:
    return DebtModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        creditor_name=domain.creditor_name,
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
