"""Mapper Tag DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/tag_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import TagModel
from modules.tags.domain.entities.tag import Tag
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: TagModel) -> Tag:
    return Tag.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: Tag) -> TagModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="TAG_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="TAG_USER_REQUIRED", message="user_id requerido")
    return TagModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        name=domain.name,
        created_at=domain.created_at,
    )
