from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.accounts.domain.entities.account import Account
from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class CreateAccountInput:
    """DTO puro de Python sin acoplamiento a Pydantic ni HTTP."""
    user_id: str
    name: str
    type: str = "OTHER"
    currency: str = "PEN"
    initial_balance: Decimal = Decimal("0.00")
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class CreateAccountOutput:
    id: str
    user_id: str
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    current_balance: Decimal
    is_default: bool
    status: str


class CreateAccountUseCase:
    """Orquesta la lógica del caso de uso. Sin dependencias de frameworks."""

    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(self, inp: CreateAccountInput) -> CreateAccountOutput:
        # 1. Validación de reglas de aplicación
        if await self._account_repo.exists_name_for_user(inp.user_id, inp.name):
            raise ConflictError(
                code="ACCOUNT_NAME_TAKEN",
                message=f"Cuenta ya existe para el usuario: {inp.name}"
            )

        # 2. Creación del Agregado de Dominio (Valida reglas puras)
        account = Account.create(
            user_id=inp.user_id,
            name=inp.name,
            type=inp.type,
            currency=inp.currency,
            initial_balance=inp.initial_balance,
            is_default=inp.is_default,
        )

        # 3. Persistencia mediante el puerto
        await self._account_repo.save(account)

        # 4. Retorno del DTO de salida
        return CreateAccountOutput(
            id=account.id,
            user_id=account.user_id,
            name=account.name,
            type=account.type.value if hasattr(account.type, "value") else str(account.type),
            currency=account.currency,
            initial_balance=account.initial_balance,
            current_balance=account.current_balance,
            is_default=account.is_default,
            status=account.status.value if hasattr(account.status, "value") else str(account.status),
        )
