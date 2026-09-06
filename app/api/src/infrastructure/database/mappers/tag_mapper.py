from __future__ import annotations

import uuid
from infrastructure.database.models import TagModel
from modules.tags.domain.entities.tag import Tag


def to_domain(model: TagModel) -> Tag:
    return Tag.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: Tag) -> TagModel:
    return TagModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        name=domain.name,
        created_at=domain.created_at,
    )


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
