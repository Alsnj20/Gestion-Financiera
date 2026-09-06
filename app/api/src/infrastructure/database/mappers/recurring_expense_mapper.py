from __future__ import annotations

import uuid

from infrastructure.database.models import RecurringExpenseModel
from modules.recurring_expenses.domain.entities.recurring_expense import (
    RecurringExpense,
)
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: RecurringExpenseModel) -> RecurringExpense:
    return RecurringExpense(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        account_id=str(model.account_id) if model.account_id else "",
        category_id=str(model.category_id) if model.category_id else "",
        amount=getattr(model, "amount", 0),
        frequency=getattr(model, "frequency", "MONTHLY"),
        next_date=getattr(model, "next_date", None),
        description=getattr(model, "description", ""),
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: RecurringExpense) -> RecurringExpenseModel:
    return RecurringExpenseModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        account_id=uuid.UUID(domain.account_id)
        if _is_uuid(domain.account_id)
        else uuid.uuid4(),
        category_id=uuid.UUID(domain.category_id)
        if _is_uuid(domain.category_id)
        else None,
        amount=domain.amount,
        frequency=domain.frequency.value
        if hasattr(domain.frequency, "value")
        else str(domain.frequency),
        next_date=domain.next_date,
        description=domain.description,
        status=domain.status,
        created_at=domain.created_at,
    )
