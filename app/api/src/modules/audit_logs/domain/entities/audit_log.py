from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.errors import ValidationError

MAX_ENTITY_TYPE_LEN = 40
MAX_ENTITY_ID_LEN = 80
MAX_ACTION_LEN = 20
MAX_SOURCE_LEN = 20


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="AL_ID_REQUIRED", message="id requerido")
    return cleaned


@dataclass(slots=True, frozen=True)
class AuditLog:
    """Append-only: sin update ni delete en ningún nivel."""

    id: str
    user_id: str
    entity_type: str
    entity_id: str
    action: str
    old_value: dict | None
    new_value: dict | None
    source: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="AL_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        entity_type = clean_str(self.entity_type)[:MAX_ENTITY_TYPE_LEN]
        if not entity_type:
            raise ValidationError(
                code="AL_ENTITY_TYPE_REQUIRED", message="entity_type requerido"
            )
        object.__setattr__(self, "entity_type", entity_type)
        entity_id = clean_str(self.entity_id)[:MAX_ENTITY_ID_LEN]
        if not entity_id:
            raise ValidationError(
                code="AL_ENTITY_ID_REQUIRED", message="entity_id requerido"
            )
        object.__setattr__(self, "entity_id", entity_id)
        action = clean_str(self.action)[:MAX_ACTION_LEN]
        if not action:
            raise ValidationError(code="AL_ACTION_REQUIRED", message="action requerido")
        object.__setattr__(self, "action", action)
        object.__setattr__(
            self,
            "source",
            clean_str(self.source, "MANUAL")[:MAX_SOURCE_LEN] or "MANUAL",
        )
        if self.old_value is not None and not isinstance(self.old_value, dict):
            object.__setattr__(self, "old_value", None)
        if self.new_value is not None and not isinstance(self.new_value, dict):
            object.__setattr__(self, "new_value", None)

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
        source: str = "MANUAL",
    ) -> AuditLog:
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            source=source,
            created_at=_utcnow(),
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        entity_type: object,
        entity_id: object,
        action: object,
        old_value: object = None,
        new_value: object = None,
        source: object = "MANUAL",
        created_at: object = None,
    ) -> AuditLog:
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            entity_type=clean_str(entity_type, ""),
            entity_id=clean_str(entity_id, ""),
            action=clean_str(action, ""),
            old_value=old_value if isinstance(old_value, dict) else None,
            new_value=new_value if isinstance(new_value, dict) else None,
            source=clean_str(source, "MANUAL"),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
        )
