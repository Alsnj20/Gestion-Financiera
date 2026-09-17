from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.errors import ValidationError

MAX_NAME_LEN = 40
_TAG_RE = re.compile(r"^[a-z0-9_]+$", re.IGNORECASE)


def normalize_tag_name(name: object) -> str:
    """Canónico: trim + sin # inicial + minúsculas (misma que el repo)."""
    return clean_str(name).lstrip("#").lower()


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="TAG_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_name(name: object) -> str:
    text = normalize_tag_name(name)
    if not text:
        raise ValidationError(code="TAG_NAME_REQUIRED", message="name requerido")
    if len(text) > MAX_NAME_LEN:
        raise ValidationError(
            code="TAG_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}"
        )
    if not _TAG_RE.match(text):
        raise ValidationError(code="TAG_NAME_INVALID", message=f"tag inválido: {text}")
    return text


@dataclass(slots=True, frozen=True)
class Tag:
    id: str
    user_id: str
    name: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="TAG_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "name", _validate_name(self.name))

    @classmethod
    def create(cls, *, user_id: str, name: str) -> Tag:
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            created_at=_utcnow(),
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        name: object,
        created_at: object = None,
    ) -> Tag:
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            name=clean_str(name, ""),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
        )

    def rename(self, name: str) -> Tag:
        return self._with(name=_validate_name(name))

    def _with(self, **kwargs: object) -> Tag:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at,
        }
        data.update(kwargs)
        return Tag(**data)  # type: ignore[arg-type]
