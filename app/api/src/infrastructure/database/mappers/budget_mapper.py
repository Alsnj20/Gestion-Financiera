from __future__ import annotations

import uuid

from infrastructure.database.models import BudgetModel
from modules.budgets.domain.entities.budget import Budget
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: BudgetModel) -> Budget:
    return Budget.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        amount=getattr(model, "amount", 0),
        period_start=getattr(model, "period_start", None),
        period_end=getattr(model, "period_end", None),
        category_id=str(model.category_id) if model.category_id else "",
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: Budget) -> BudgetModel:
    return BudgetModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        name=domain.name,
        amount=domain.amount,
        period_start=domain.period_start,
        period_end=domain.period_end,
        category_id=uuid.UUID(domain.category_id)
        if domain.category_id and _is_uuid(domain.category_id)
        else None,
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
    )
