from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.errors import ValidationError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class AuditLog:
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
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.entity_type = _safe_str(self.entity_type)
        self.entity_id = _safe_str(self.entity_id)
        self.action = _safe_str(self.action)
        self.source = _safe_str(self.source, "MANUAL")

        if not self.user_id:
            raise ValidationError(code="AL_USER_REQUIRED", message="user_id requerido")
        if not self.entity_type:
            raise ValidationError(code="AL_ENTITY_TYPE_REQUIRED", message="entity_type requerido")
        if not self.entity_id:
            raise ValidationError(code="AL_ENTITY_ID_REQUIRED", message="entity_id requerido")
        if not self.action:
            raise ValidationError(code="AL_ACTION_REQUIRED", message="action requerido")

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
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            source=source,
            created_at=now,
        )

    @classmethod
    def rehydrate(cls, **kwargs: object) -> AuditLog:
        return cls(
            id=_safe_str(kwargs.get("id")) or str(uuid.uuid4()),
            user_id=_safe_str(kwargs.get("user_id"), ""),
            entity_type=_safe_str(kwargs.get("entity_type"), ""),
            entity_id=_safe_str(kwargs.get("entity_id"), ""),
            action=_safe_str(kwargs.get("action"), ""),
            old_value=kwargs.get("old_value") if isinstance(kwargs.get("old_value"), dict) else None,
            new_value=kwargs.get("new_value") if isinstance(kwargs.get("new_value"), dict) else None,
            source=_safe_str(kwargs.get("source"), "MANUAL"),
            created_at=kwargs.get("created_at") if isinstance(kwargs.get("created_at"), datetime) else _utcnow(),
        )
