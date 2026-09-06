from __future__ import annotations

import uuid
from infrastructure.database.models import PaymentMethodModel
from modules.payment_methods.domain.entities.payment_method import PaymentMethod


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
    return PaymentMethodModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        account_id=uuid.UUID(domain.account_id) if _is_uuid(domain.account_id) else uuid.uuid4(),
        name=domain.name,
        type=domain.type,
        is_default=domain.is_default,
        status=domain.status.value if hasattr(domain.status, "value") else str(domain.status),
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
