"""Mapper Account DB <-> dominio. Vive en el módulo (fuente única)."""

from __future__ import annotations

import uuid

from infrastructure.database.models import AccountModel
from modules.accounts.domain.entities.account import Account
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: AccountModel) -> Account:
    """Converts a database model to a domain entity."""
    return Account.rehydrate(
        id=str(model.id),
        user_id=str(model.user_id),
        name=model.name,
        type=model.type,
        currency=model.currency,
        initial_balance=model.initial_balance,
        current_balance=model.current_balance,
        is_default=model.is_default,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(domain: Account) -> AccountModel:
    """Converts a domain entity to a database model."""
    return AccountModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        name=domain.name,
        type=domain.type.value,
        currency=domain.currency,
        initial_balance=domain.initial_balance,
        current_balance=domain.current_balance,
        is_default=domain.is_default,
        status=domain.status.value,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
