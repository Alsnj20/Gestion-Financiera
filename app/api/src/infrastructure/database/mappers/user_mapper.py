from __future__ import annotations

import uuid

from infrastructure.database.models import UserModel
from modules.users.domain.entities.user import User


def to_domain(model: UserModel) -> User:
    """Convierte fila de BD a entidad de dominio."""
    return User.rehydrate(
        id=str(model.id) if model.id else "",
        name=getattr(model, "name", ""),
        phone=getattr(model, "phone", ""),
        email=getattr(model, "email", "") or "",
        timezone=getattr(model, "timezone", "America/Lima") or "America/Lima",
        currency=getattr(model, "currency", "PEN") or "PEN",
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: User) -> UserModel:
    """Convierte entidad a fila de BD."""
    return UserModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        name=domain.name,
        phone=domain.phone,
        email=domain.email or "",
        timezone=domain.timezone,
        currency=domain.currency,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def update_model(model: UserModel, domain: User) -> None:
    model.name = domain.name
    model.phone = domain.phone
    model.email = domain.email or ""
    model.timezone = domain.timezone
    model.currency = domain.currency
    model.updated_at = domain.updated_at


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
