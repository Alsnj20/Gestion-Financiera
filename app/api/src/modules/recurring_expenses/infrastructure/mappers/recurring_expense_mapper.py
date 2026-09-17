"""Mapper RecurringExpense DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/recurring_expense_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import RecurringExpenseModel
from modules.recurring_expenses.domain.entities.recurring_expense import (
    RecurringExpense,
)
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: RecurringExpenseModel) -> RecurringExpense:
    return RecurringExpense.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        account_id=str(model.account_id) if model.account_id else "",
        category_id=str(model.category_id) if model.category_id else "",
        amount=getattr(model, "amount", 0),
        frequency=getattr(model, "frequency", "MONTHLY"),
        next_date=getattr(model, "next_date", None),
        description=getattr(model, "description", "") or "",
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: RecurringExpense) -> RecurringExpenseModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="RE_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="RE_USER_REQUIRED", message="user_id requerido")
    if not _is_uuid(domain.account_id):
        raise ValidationError(
            code="RE_ACCOUNT_REQUIRED", message="account_id requerido"
        )
    return RecurringExpenseModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        account_id=uuid.UUID(domain.account_id),
        category_id=uuid.UUID(domain.category_id)
        if domain.category_id and _is_uuid(domain.category_id)
        else None,
        amount=domain.amount,
        frequency=domain.frequency.value
        if hasattr(domain.frequency, "value")
        else str(domain.frequency),
        next_date=domain.next_date,
        description=domain.description or "",
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
    )
