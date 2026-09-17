"""Mapper Limit DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/limit_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import LimitModel
from modules.limits.domain.entities.limit import Limit
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: LimitModel) -> Limit:
    return Limit.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        amount=getattr(model, "amount", 0),
        period_type=getattr(model, "period_type", "MONTHLY"),
        category_id=str(model.category_id) if model.category_id else "",
        threshold_warning=getattr(model, "threshold_warning", 80),
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Limit) -> LimitModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="LIMIT_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="LIMIT_USER_REQUIRED", message="user_id requerido")
    return LimitModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        name=domain.name,
        amount=domain.amount,
        period_type=domain.period_type.value
        if hasattr(domain.period_type, "value")
        else str(domain.period_type),
        category_id=uuid.UUID(domain.category_id)
        if domain.category_id and _is_uuid(domain.category_id)
        else None,
        threshold_warning=domain.threshold_warning,
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
