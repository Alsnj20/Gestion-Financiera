"""Mapper Category DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/category_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import CategoryModel
from modules.categories.domain.entities.category import Category
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: CategoryModel) -> Category:
    return Category.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        type=getattr(model, "type", "BOTH"),
        parent_id=str(model.parent_id) if model.parent_id else "",
        icon=getattr(model, "icon", "") or "",
        color=getattr(model, "color", "") or "",
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Category) -> CategoryModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="CAT_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="CAT_USER_REQUIRED", message="user_id requerido")
    return CategoryModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        name=domain.name,
        type=domain.type.value if hasattr(domain.type, "value") else str(domain.type),
        parent_id=uuid.UUID(domain.parent_id)
        if domain.parent_id and _is_uuid(domain.parent_id)
        else None,
        icon=domain.icon or "",
        color=domain.color or "",
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
