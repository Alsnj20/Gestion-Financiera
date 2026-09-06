from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.accounts.application.dtos import AccountOutput, CreateAccountOutput
from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.accounts.domain.entities.account import Account
from shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class CreateAccountInput:
    user_id: str
    name: str
    type: str = "OTHER"
    currency: str = "PEN"
    initial_balance: Decimal = Decimal("0.00")
    is_default: bool = False


class CreateAccountUseCase:
    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(self, inp: CreateAccountInput) -> CreateAccountOutput:
        # Validar nombre único
        if await self._account_repo.exists_name_for_user(inp.user_id, inp.name):
            raise ConflictError(
                code="ACCOUNT_NAME_TAKEN",
                message=f"Cuenta ya existe para el usuario: {inp.name}",
            )

        # Si se marca como default, desmarcar las demás
        if inp.is_default:
            await self._account_repo.clear_default_for_user(inp.user_id)

        # Crear cuenta
        account = Account.create(
            user_id=inp.user_id,
            name=inp.name,
            type=inp.type,
            currency=inp.currency,
            initial_balance=inp.initial_balance,
            is_default=inp.is_default,
        )

        await self._account_repo.save(account)

        return AccountOutput(
            id=account.id,
            user_id=account.user_id,
            name=account.name,
            type=account.type.value,
            currency=account.currency,
            initial_balance=account.initial_balance,
            current_balance=account.current_balance,
            is_default=account.is_default,
            status=account.status.value,
        )
