from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from shared.domain.guards import clean_str
from shared.domain.guards import utcnow as _utcnow
from shared.errors import ValidationError

_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_NAME_LEN = 120


def _validate_name(name: str) -> str:
    name = clean_str(name)
    if not name:
        raise ValidationError(
            code="USER_NAME_REQUIRED", message="El nombre es requerido"
        )
    if len(name) > MAX_NAME_LEN:
        raise ValidationError(
            code="USER_NAME_TOO_LONG",
            message=f"El nombre excede {MAX_NAME_LEN} caracteres",
        )
    return name


def _validate_phone(phone: str) -> str:
    phone = clean_str(phone)
    if not _PHONE_RE.match(phone):
        raise ValidationError(
            code="USER_PHONE_INVALID", message=f"Teléfono inválido: {phone}"
        )
    return phone


def _validate_email(email: object) -> str:
    email = clean_str(email).lower()
    if email and not _EMAIL_RE.match(email):
        raise ValidationError(
            code="USER_EMAIL_INVALID", message=f"Email inválido: {email}"
        )
    return email


@dataclass(frozen=True, slots=True)
class User:
    id: str
    name: str
    phone: str
    email: str = ""
    role: str = "USER"
    is_verified: bool = False
    google_id: str = ""
    timezone: str = "America/Lima"
    currency: str = "PEN"
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", clean_str(self.id))
        object.__setattr__(self, "name", _validate_name(self.name))
        object.__setattr__(self, "phone", _validate_phone(self.phone))
        object.__setattr__(self, "email", _validate_email(self.email))
        role = clean_str(self.role, "USER").upper()
        object.__setattr__(self, "role", role if role in ("USER", "ADMIN") else "USER")
        object.__setattr__(self, "google_id", clean_str(self.google_id))
        object.__setattr__(self, "timezone", clean_str(self.timezone, "America/Lima"))
        currency = clean_str(self.currency, "PEN").upper()
        object.__setattr__(self, "currency", currency or "PEN")

    @classmethod
    def create(
        cls,
        *,
        name: str,
        phone: str,
        email: str = "",
        role: str = "USER",
        is_verified: bool = False,
        google_id: str = "",
        timezone: str = "America/Lima",
        currency: str = "PEN",
    ) -> User:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            phone=phone,
            email=email,
            role=role,
            is_verified=is_verified,
            google_id=google_id,
            timezone=timezone,
            currency=currency,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def rehydrate(
        cls,
        *,
        id: str,
        name: str,
        phone: str,
        email: str = "",
        role: str = "USER",
        is_verified: bool = False,
        google_id: str = "",
        timezone: str = "America/Lima",
        currency: str = "PEN",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> User:
        return cls(
            id=id,
            name=name,
            phone=phone,
            email=email,
            role=role,
            is_verified=is_verified,
            google_id=google_id,
            timezone=timezone,
            currency=currency,
            created_at=created_at if isinstance(created_at, datetime) else _utcnow(),
            updated_at=updated_at if isinstance(updated_at, datetime) else _utcnow(),
        )

    def update_profile(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        timezone: str | None = None,
        currency: str | None = None,
    ) -> User:
        return self._with(
            name=_validate_name(name) if name is not None else self.name,
            email=_validate_email(email) if email is not None else self.email,
            timezone=clean_str(timezone, self.timezone)
            if timezone is not None
            else self.timezone,
            currency=(
                clean_str(currency, self.currency).upper()
                if currency is not None
                else self.currency
            ),
        )

    def verify(self) -> User:
        return self._with(is_verified=True)

    def _with(self, **kwargs: object) -> User:  # type: ignore[no-untyped-def]
        data: dict[str, object] = {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "is_verified": self.is_verified,
            "google_id": self.google_id,
            "timezone": self.timezone,
            "currency": self.currency,
            "created_at": self.created_at,
            "updated_at": _utcnow(),
        }
        data.update(kwargs)
        return User(**data)  # type: ignore[arg-type]
