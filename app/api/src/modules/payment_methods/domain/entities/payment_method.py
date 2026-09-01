from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.errors import ValidationError
from shared.types.enums import AccountStatus

MAX_NAME_LEN = 60


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_str(v: object, default: str = "") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


@dataclass(slots=True)
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
        self.id = _safe_str(self.id) or str(uuid.uuid4())
        self.user_id = _safe_str(self.user_id)
        self.account_id = _safe_str(self.account_id)
        self.name = _safe_str(self.name)
        self.type = _safe_str(self.type, "")
        self.status = AccountStatus.safe(self.status)
        self.is_default = bool(self.is_default) if self.is_default is not None else False

        if not self.user_id:
            raise ValidationError(code="PM_USER_REQUIRED", message="user_id requerido")
        if not self.account_id:
            raise ValidationError(code="PM_ACCOUNT_REQUIRED", message="account_id requerido")
        if not self.name:
            raise ValidationError(code="PM_NAME_REQUIRED", message="name requerido")
        if len(self.name) > MAX_NAME_LEN:
            raise ValidationError(code="PM_NAME_TOO_LONG", message=f"name excede {MAX_NAME_LEN}")

    @classmethod
    def create(cls, *, user_id: str, account_id: str, name: str, type: str = "", is_default: bool = False) -> PaymentMethod:
        now = _utcnow()
        return cls(id=str(uuid.uuid4()), user_id=user_id, account_id=account_id, name=name, type=type, is_default=is_default, status=AccountStatus.ACTIVE, created_at=now, updated_at=now)

    @classmethod
    def rehydrate(cls, *, id: object, user_id: object, account_id: object, name: object, type: object = "", is_default: object = False, status: object = AccountStatus.ACTIVE, created_at: object = None, updated_at: object = None) -> PaymentMethod:
        return cls(
            id=_safe_str(id) or str(uuid.uuid4()),
            user_id=_safe_str(user_id, ""),
            account_id=_safe_str(account_id, ""),
            name=_safe_str(name, "Unknown"),
            type=_safe_str(type, ""),
            is_default=bool(is_default) if is_default is not None else False,
            status=AccountStatus.safe(status),
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def archive(self) -> PaymentMethod:
        return PaymentMethod(id=self.id, user_id=self.user_id, account_id=self.account_id, name=self.name, type=self.type, is_default=False, status=AccountStatus.ARCHIVED, created_at=self.created_at, updated_at=_utcnow())
