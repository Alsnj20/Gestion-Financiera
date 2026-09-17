"""Mapper PaymentMethod DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/payment_method_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import PaymentMethodModel
from modules.payment_methods.domain.entities.payment_method import PaymentMethod
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: PaymentMethodModel) -> PaymentMethod:
    return PaymentMethod.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        account_id=str(model.account_id) if model.account_id else "",
        name=getattr(model, "name", ""),
        type=getattr(model, "type", ""),
        is_default=getattr(model, "is_default", False),
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: PaymentMethod) -> PaymentMethodModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="PM_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="PM_USER_REQUIRED", message="user_id requerido")
    if not _is_uuid(domain.account_id):
        raise ValidationError(
            code="PM_ACCOUNT_REQUIRED", message="account_id requerido"
        )
    return PaymentMethodModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        account_id=uuid.UUID(domain.account_id),
        name=domain.name,
        type=domain.type,
        is_default=domain.is_default,
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
