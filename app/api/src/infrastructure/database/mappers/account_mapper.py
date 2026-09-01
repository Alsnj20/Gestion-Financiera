from __future__ import annotations

import uuid

from infrastructure.database.models import AccountModel
from modules.accounts.domain.entities.account import Account


def to_domain(model: AccountModel) -> Account:
    """Converts a database model to a domain entity."""
    return Account.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        type=getattr(model, "type", "OTHER"),
        currency=getattr(model, "currency", "PEN"),
        initial_balance=getattr(model, "initial_balance", 0),
        current_balance=getattr(model, "current_balance", None),
        is_default=getattr(model, "is_default", False),
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Account) -> AccountModel:
    """Converts a domain entity to a database model."""
    return AccountModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        name=domain.name,
        type=domain.type.value if hasattr(domain.type, "value") else str(domain.type),
        currency=domain.currency,
        initial_balance=domain.initial_balance,
        current_balance=domain.current_balance,
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
