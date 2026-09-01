from __future__ import annotations

from dataclasses import dataclass
from modules.users.domain.entities.user import User
from modules.users.domain.ports.user_repository import UserRepositoryPort
from shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class CreateUserInput:
    """DTO puro de Python sin acoplamiento a Pydantic ni HTTP."""
    name: str
    phone: str
    email: str = ""
    timezone: str = "America/Lima"
    currency: str = "PEN"


@dataclass(frozen=True, slots=True)
class CreateUserOutput:
    id: str
    name: str
    phone: str
    email: str
    timezone: str
    currency: str


class CreateUserUseCase:
    """Orquesta la lógica del caso de uso. Sin dependencias de frameworks."""

    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, inp: CreateUserInput) -> CreateUserOutput:
        # 1. Validación de reglas de aplicación
        if await self._user_repo.exists_by_phone(inp.phone):
            raise ConflictError(code="USER_PHONE_TAKEN", message=f"Teléfono ya registrado: {inp.phone}")

        email = inp.email.strip().lower() if inp.email else ""
        if email:
            existing_email = await self._user_repo.find_by_email(email)
            if existing_email:
                raise ConflictError(code="USER_EMAIL_TAKEN", message=f"Email ya vinculado: {email}")

        # 2. Creación del Agregado de Dominio (Valida reglas puras)
        user = User.create(
            name=inp.name,
            phone=inp.phone,
            email=email,
            timezone=inp.timezone,
            currency=inp.currency,
        )

        # 3. Persistencia mediante el puerto
        await self._user_repo.save(user)

        # 4. Retorno del DTO de salida
        return CreateUserOutput(
            id=user.id,
            name=user.name,
            phone=user.phone,
            email=user.email,
            timezone=user.timezone,
            currency=user.currency,
        )
