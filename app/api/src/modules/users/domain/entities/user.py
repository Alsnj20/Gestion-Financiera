from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.errors import ValidationError

# Value objects for validation
_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

# slot = save memory, faster attribute access, but no dynamic attributes allowed
# frozen = immutable, but we want to allow updates via methods that return new instances
@dataclass(frozen=True, slots=True)
class User:
    """Agregado User — Entidad de dominio pura e inmutable."""

    id: str
    name: str
    phone: str
    email: str = ""
    password_hash: str = ""
    timezone: str = "America/Lima"
    currency: str = "PEN"
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or len(self.name.strip()) == 0:
            raise ValidationError(code="USER_NAME_REQUIRED", message="El nombre es requerido")
        if len(self.name) > 120:
            raise ValidationError(code="USER_NAME_TOO_LONG", message="El nombre excede 120 caracteres")
        if not _PHONE_RE.match(self.phone):
            raise ValidationError(code="USER_PHONE_INVALID", message=f"Teléfono inválido: {self.phone}")
        if self.email and not _EMAIL_RE.match(self.email):
            raise ValidationError(code="USER_EMAIL_INVALID", message=f"Email inválido: {self.email}")

    @classmethod
    def create(
        cls,
        *,
        name: str,
        phone: str,
        email: str = "",
        password_hash: str = "",
        timezone: str = "America/Lima",
        currency: str = "PEN",
    ) -> User:
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            timezone=timezone.strip(),
            currency=currency.strip().upper(),
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
        password_hash: str = "",
        timezone: str = "America/Lima",
        currency: str = "PEN",
        created_at: datetime,
        updated_at: datetime,
    ) -> User:
        return cls(
            id=id,
            name=name,
            phone=phone,
            email=email,
            password_hash=password_hash,
            timezone=timezone,
            currency=currency,
            created_at=created_at,
            updated_at=updated_at,
        )

    def update_profile(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        timezone: str | None = None,
        currency: str | None = None,
    ) -> User:
        return User(
            id=self.id,
            name=name.strip() if name is not None else self.name,
            phone=self.phone,
            email=email.strip().lower() if email is not None else self.email,
            password_hash=self.password_hash,
            timezone=timezone.strip() if timezone is not None else self.timezone,
            currency=currency.strip().upper() if currency is not None else self.currency,
            created_at=self.created_at,
            updated_at=_utcnow(),
        )
