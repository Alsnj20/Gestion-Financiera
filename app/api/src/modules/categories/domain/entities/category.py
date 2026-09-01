from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.errors import ValidationError
from shared.types.enums import CategoryStatus, CategoryType

MAX_NAME_LEN = 80


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
class Category:
    id: str
    user_id: str
    name: str
    type: CategoryType = CategoryType.BOTH
    parent_id: str = ""  # "" significa raíz; evita null
    status: CategoryStatus = CategoryStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.name = _safe_str(self.name)
        self.parent_id = _safe_str(self.parent_id, "")
        self.type = CategoryType.safe(self.type)
        self.status = CategoryStatus.safe(self.status)

        if not self.user_id:
            raise ValidationError(code="CAT_USER_REQUIRED", message="user_id requerido")
        if not self.name:
            raise ValidationError(code="CAT_NAME_REQUIRED", message="name requerido")
        if len(self.name) > MAX_NAME_LEN:
            raise ValidationError(code="CAT_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}")
        if self.parent_id == self.id:
            raise ValidationError(code="CAT_SELF_PARENT", message="parent_id no puede ser igual a id")

    @classmethod
    def create(cls, *, user_id: str, name: str, type: CategoryType | str = CategoryType.BOTH, parent_id: str = "") -> Category:
        now = _utcnow()
        return cls(id=str(uuid.uuid4()), user_id=user_id, name=name, type=CategoryType.safe(type), parent_id=_safe_str(parent_id, ""), status=CategoryStatus.ACTIVE, created_at=now, updated_at=now)

    @classmethod
    def rehydrate(cls, *, id: object, user_id: object, name: object, type: object = CategoryType.BOTH, parent_id: object = "", status: object = CategoryStatus.ACTIVE, created_at: object = None, updated_at: object = None) -> Category:
        return cls(
            id=_safe_str(id) or str(uuid.uuid4()),
            user_id=_safe_str(user_id, ""),
            name=_safe_str(name, "Unknown"),
            type=CategoryType.safe(type),
            parent_id=_safe_str(parent_id, ""),
            status=CategoryStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    @property
    def is_root(self) -> bool:
        return not self.parent_id

    def archive(self) -> Category:
        return Category(id=self.id, user_id=self.user_id, name=self.name, type=self.type, parent_id=self.parent_id, status=CategoryStatus.ARCHIVED, created_at=self.created_at, updated_at=_utcnow())
