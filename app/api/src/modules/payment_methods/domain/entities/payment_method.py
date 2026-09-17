from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from shared.domain.guards import clean_str
from shared.domain.guards import shadow_name as _shadow_name
from shared.domain.guards import utcnow as _utcnow
from shared.domain.guards import validate_bool as _validate_bool
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import AccountStatus

MAX_NAME_LEN = 60
MAX_TYPE_LEN = 60


def _validate_id(value: object) -> str:
    cleaned = clean_str(value)
    if not cleaned:
        raise ValidationError(code="PM_ID_REQUIRED", message="id requerido")
    return cleaned


def _validate_name(name: object) -> str:
    text = clean_str(name)
    if not text:
        raise ValidationError(code="PM_NAME_REQUIRED", message="name requerido")
    if len(text) > MAX_NAME_LEN:
        raise ValidationError(
            code="PM_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}"
        )
    return text


@dataclass(slots=True, frozen=True)
class PaymentMethod:
    id: str
    user_id: str
    account_id: str
    name: str
    type: str = ""
    is_default: bool = False
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_id(self.id))
        user_id = clean_str(self.user_id)
        if not user_id:
            raise ValidationError(code="PM_USER_REQUIRED", message="user_id requerido")
        object.__setattr__(self, "user_id", user_id)
        account_id = clean_str(self.account_id)
        if not account_id:
            raise ValidationError(
                code="PM_ACCOUNT_REQUIRED", message="account_id requerido"
            )
        object.__setattr__(self, "account_id", account_id)
        object.__setattr__(self, "name", _validate_name(self.name))
        object.__setattr__(self, "type", clean_str(self.type)[:MAX_TYPE_LEN])
        object.__setattr__(self, "status", AccountStatus.safe(self.status))
        object.__setattr__(
            self,
            "is_default",
            _validate_bool(self.is_default, "is_default", prefix="PM"),
        )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        account_id: str,
        name: str,
        type: str = "",
        is_default: bool = False,
    ) -> PaymentMethod:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            name=name,
            type=type,
            is_default=is_default,
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: object,
        user_id: object,
        account_id: object,
        name: object,
        type: object = "",
        is_default: object = False,
        status: object = AccountStatus.ACTIVE,
        created_at: object = None,
        updated_at: object = None,
    ) -> PaymentMethod:
        return cls(
            id=clean_str(id),
            user_id=clean_str(user_id, ""),
            account_id=clean_str(account_id, ""),
            name=clean_str(name, ""),
            type=clean_str(type, ""),
            is_default=is_default,
            status=AccountStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def is_archived(self) -> bool:
        return self.status == AccountStatus.ARCHIVED

    def archive(self) -> PaymentMethod:
        if self.is_archived():
            return self
        return self._with(status=AccountStatus.ARCHIVED, is_default=False)

    def archive_with_shadow_name(self) -> PaymentMethod:
        """Libera el nombre original para recrearlo (único por usuario)."""
        shadowed = _shadow_name(self.name, self.id, MAX_NAME_LEN, fallback="método")
        return self.archive()._with(name=shadowed)

    def restore(self, name: str) -> PaymentMethod:
        if not self.is_archived():
            raise BusinessRuleError(
                code="PM_NOT_ARCHIVED",
                message="Solo se puede restaurar un método archivado.",
            )
        return self._with(name=_validate_name(name), status=AccountStatus.ACTIVE)

    def rename(self, name: str) -> PaymentMethod:
        self._ensure_active("editarse")
        return self._with(name=_validate_name(name))

    def change_type(self, method_type: str) -> PaymentMethod:
        self._ensure_active("editarse")
        return self._with(type=clean_str(method_type)[:MAX_TYPE_LEN])

    def change_account(self, account_id: str) -> PaymentMethod:
        self._ensure_active("editarse")
        new_account = clean_str(account_id)
        if not new_account:
            raise ValidationError(
                code="PM_ACCOUNT_REQUIRED", message="account_id requerido"
            )
        return self._with(account_id=new_account)

    def mark_as_default(self) -> PaymentMethod:
        self._ensure_active("marcarse como default")
        return self._with(is_default=True)

    def unmark_as_default(self) -> PaymentMethod:
        return self._with(is_default=False)

    def _ensure_active(self, action_description: str) -> None:
        if self.is_archived():
            raise BusinessRuleError(
                code="PM_ARCHIVED",
                message=f"Método archivado no puede {action_description}.",
            )

    def _with(self, **kwargs: object) -> PaymentMethod:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "name": self.name,
            "type": self.type,
            "is_default": self.is_default,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return PaymentMethod(**data)  # type: ignore[arg-type]
