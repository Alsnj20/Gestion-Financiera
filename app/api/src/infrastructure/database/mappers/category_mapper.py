from __future__ import annotations

import uuid
from infrastructure.database.models import CategoryModel
from modules.categories.domain.entities.category import Category


def to_domain(model: CategoryModel) -> Category:
    return Category.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        name=getattr(model, "name", ""),
        type=getattr(model, "type", "BOTH"),
        parent_id=str(model.parent_id) if model.parent_id else "",
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Category) -> CategoryModel:
    return CategoryModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        name=domain.name,
        type=domain.type.value if hasattr(domain.type, "value") else str(domain.type),
        parent_id=uuid.UUID(domain.parent_id) if domain.parent_id and _is_uuid(domain.parent_id) else None,
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
