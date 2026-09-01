from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.errors import ValidationError

MAX_NAME_LEN = 40
_TAG_RE = re.compile(r"^[a-z0-9_]+$", re.IGNORECASE)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip().lstrip("#")
    return s if s else default


@dataclass(slots=True)
class Tag:
    id: str
    user_id: str
    name: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.name = _safe_str(self.name).lower()
        if not self.user_id:
            raise ValidationError(code="TAG_USER_REQUIRED", message="user_id requerido")
        if not self.name:
            raise ValidationError(code="TAG_NAME_REQUIRED", message="name requerido")
        if len(self.name) > MAX_NAME_LEN:
            raise ValidationError(code="TAG_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}")
        if not _TAG_RE.match(self.name):
            raise ValidationError(code="TAG_NAME_INVALID", message=f"tag inválido: {self.name}")

    @classmethod
    def create(cls, *, user_id: str, name: str) -> Tag:
        return cls(id=str(uuid.uuid4()), user_id=user_id, name=name, created_at=_utcnow())

    @classmethod
    def rehydrate(cls, *, id: object, user_id: object, name: object, created_at: object = None) -> Tag:
        return cls(id=_safe_str(id) or str(uuid.uuid4()), user_id=_safe_str(user_id, ""), name=_safe_str(name, "unknown"), created_at=created_at if isinstance(created_at, datetime) else _utcnow())
