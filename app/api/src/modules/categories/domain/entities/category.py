from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from shared.domain.guards import clean_str
from shared.domain.guards import shadow_name as _shadow_name
from shared.domain.guards import utcnow as _utcnow
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import CategoryStatus, CategoryType

MAX_NAME_LEN = 80


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="CAT_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_name(name: object) -> str:
    text = clean_str(name)
    if not text:
        raise ValidationError(code="CAT_NAME_REQUIRED", message="name requerido")
    if len(text) > MAX_NAME_LEN:
        raise ValidationError(
            code="CAT_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}"
        )
    return text


@dataclass(slots=True, frozen=True)
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
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="CAT_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "name", _validate_name(self.name))
        object.__setattr__(self, "parent_id", clean_str(self.parent_id))
        object.__setattr__(self, "type", CategoryType.safe(self.type))
        object.__setattr__(self, "status", CategoryStatus.safe(self.status))
        if self.parent_id == self.id:
            raise ValidationError(
                code="CAT_SELF_PARENT", message="parent_id no puede ser igual a id"
            )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        name: str,
        type: CategoryType | str = CategoryType.BOTH,
        parent_id: str = "",
    ) -> Category:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            type=CategoryType.safe(type),
            parent_id=clean_str(parent_id),
            status=CategoryStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        name: object,
        type: object = CategoryType.BOTH,
        parent_id: object = "",
        status: object = CategoryStatus.ACTIVE,
        created_at: object = None,
        updated_at: object = None,
    ) -> Category:
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            name=clean_str(name, ""),
            type=CategoryType.safe(type),
            parent_id=clean_str(parent_id, ""),
            status=CategoryStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    @property
    def is_root(self) -> bool:
        return not self.parent_id

    def is_archived(self) -> bool:
        return self.status == CategoryStatus.ARCHIVED

    def archive(self) -> Category:
        if self.is_archived():
            return self
        return self._with(status=CategoryStatus.ARCHIVED)

    def archive_with_shadow_name(self) -> Category:
        """Libera el nombre original para recrearlo (caso WhatsApp)."""
        shadowed = _shadow_name(self.name, self.id, MAX_NAME_LEN, fallback="categoría")
        return self.archive()._with(name=shadowed)

    def restore(self, name: str) -> Category:
        if not self.is_archived():
            raise BusinessRuleError(
                code="CAT_NOT_ARCHIVED",
                message="Solo se puede restaurar una categoría archivada.",
            )
        return self._with(name=_validate_name(name), status=CategoryStatus.ACTIVE)

    def rename(self, name: str) -> Category:
        self._ensure_active("editarse")
        return self._with(name=_validate_name(name))

    def change_type(self, category_type: CategoryType | str) -> Category:
        self._ensure_active("editarse")
        return self._with(type=CategoryType.safe(category_type))

    def reparent(self, parent_id: str | None) -> Category:
        self._ensure_active("editarse")
        new_parent = clean_str(parent_id)
        if new_parent == self.id:
            raise ValidationError(
                code="CAT_SELF_PARENT", message="parent_id no puede ser igual a id"
            )
        return self._with(parent_id=new_parent)

    def _ensure_active(self, action_description: str) -> None:
        if self.is_archived():
            raise BusinessRuleError(
                code="CAT_ARCHIVED",
                message=f"Categoría archivada no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> Category:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "parent_id": self.parent_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return Category(**data)  # type: ignore[arg-type]
