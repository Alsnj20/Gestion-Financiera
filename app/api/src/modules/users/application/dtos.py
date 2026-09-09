"""DTOs de salida unificados del módulo users.

Fuente única: `UserOutput` + `to_user_output`.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.users.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class UserOutput:
    id: str
    name: str
    phone: str
    email: str
    role: str
    is_verified: bool
    timezone: str
    currency: str


def to_user_output(user: User) -> UserOutput:
    return UserOutput(
        id=user.id,
        name=user.name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
        timezone=user.timezone,
        currency=user.currency,
    )


# Aliases de compatibilidad.
GetUserOutput = UserOutput
ListUsersOutput = UserOutput
UpdateUserOutput = UserOutput
