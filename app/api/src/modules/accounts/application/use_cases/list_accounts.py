from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.accounts.application.ports.account_repository import AccountRepositoryPort


@dataclass(frozen=True, slots=True)
class AccountOutput:
    """DTO de salida para una cuenta."""
    id: str
    user_id: str
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    current_balance: Decimal
    is_default: bool
    status: str


class ListAccountsUseCase:
    """Orquesta la lógica para listar cuentas de un usuario."""

    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(self, user_id: str) -> list[AccountOutput]:
        accounts = await self._account_repo.find_by_user(user_id)
        return [
            AccountOutput(
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
            for account in accounts
        ]
